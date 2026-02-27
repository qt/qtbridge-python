# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

"""
Automatic property generation from __init__ assignments.

This module analyzes __init__ methods and automatically creates property
descriptors for simple attribute assignments.
"""

import ast
import inspect
import textwrap
from typing import Any, Set, Dict, Optional

from QtBridge import Signal
from .property_observers import collect_observers, Change

try:
    from ._build_config import _logger
except ImportError:
    import logging
    _logger = logging.getLogger("qtbridge-python")


# Sentinel used to detect the very first property write (from __init__)
_UNSET = object()

class InitAttributeFinder(ast.NodeVisitor):
    """AST visitor to find all self.attribute assignments in __init__"""

    def __init__(self):
        self.attributes: Dict[str, Any] = {}
        self.in_init = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == "__init__":
            self.in_init = True
            self.generic_visit(node)
            self.in_init = False

    def visit_Assign(self, node: ast.Assign):
        if not self.in_init:
            return

        for target in node.targets:
            # Look for self.attribute assignments
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    attr_name = target.attr

                    # Try to extract default value
                    default_value = None
                    if isinstance(node.value, ast.Constant):
                        default_value = node.value.value
                    elif isinstance(node.value, ast.List):
                        default_value = []
                    elif isinstance(node.value, ast.Dict):
                        default_value = {}

                    self.attributes[attr_name] = default_value

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Handle annotated assignments like self.counter: int = 0"""
        if not self.in_init:
            return

        if isinstance(node.target, ast.Attribute):
            if isinstance(node.target.value, ast.Name) and node.target.value.id == "self":
                attr_name = node.target.attr

                # Try to extract default value
                default_value = None
                if node.value:
                    if isinstance(node.value, ast.Constant):
                        default_value = node.value.value
                    elif isinstance(node.value, ast.List):
                        default_value = []
                    elif isinstance(node.value, ast.Dict):
                        default_value = {}

                self.attributes[attr_name] = default_value

        self.generic_visit(node)


def _get_cls_name(cls) -> str:
    return getattr(cls, "__name__", str(cls))

def find_init_attributes(cls: type) -> Dict[str, Any]:
    """
    Find all self.attribute assignments in a class's __init__ method.
    """
    if not hasattr(cls, "__init__"):
        return {}

    try:
        source = textwrap.dedent(inspect.getsource(cls.__init__))
        tree = ast.parse(source)
        finder = InitAttributeFinder()
        finder.visit(tree)
        return finder.attributes
    except (OSError, TypeError, SyntaxError):
        # Can't get source (built-in classes, classes defined inside functions, etc.)
        # SyntaxError/IndentationError can occur when inspect.getsource returns
        # source with inconsistent indentation for classes defined inside other
        # functions
        cls_name = _get_cls_name(cls)
        _logger.debug("find_init_attributes: could not parse source for %s, "
                  "skipping auto-property generation", cls_name)
        return {}

def augment_class_with_auto_properties(cls: type, exclude: Optional[Set[str]] = None) -> type:
    """
    Augment a class by adding auto-generated properties for __init__ attributes.
    This modifies the class in-place and returns it for convenience.
    """
    # Find attributes in __init__
    exclude = exclude or set()
    attributes = find_init_attributes(cls)
    cls_name = _get_cls_name(cls)

    # Collect @watch / @effect metadata
    observers = collect_observers(cls)
    _logger.debug("augment_class_with_auto_properties: %s — found raw attributes: %s",
                  cls_name, list(attributes.keys()))

    # Filter out excluded attributes, private names (starting with '_'),
    # and attributes that already have an explicit property descriptor on the class.
    # Underscore-prefixed names are private implementation details and should never
    # be auto-exposed as public QML properties.
    attributes = {
        name: default for name, default in attributes.items()
        if not name.startswith("_")
        and name not in exclude
        and not isinstance(getattr(cls, name, None), property)
    }

    for attr_name, default_value in attributes.items():
        private_name = f"_{attr_name}"

        # For info: Why do we need a custom signal here and not use the automatically
        # created one inside registerProperties()?
        # The auto created notify signal only works when the setter is called from QML.
        # If the setter is called from Python code, we need to emit the signal manually
        # to notify QML of the change.

        signal_name = f"{attr_name}Changed"
        if not hasattr(cls, signal_name):
            sig = Signal()
            setattr(cls, signal_name, sig)
            # __set_name__ is only called automatically during class body execution.
            # For dynamically added descriptors we must call it manually so the
            # signal knows its own name (otherwise signalInstance.name stays "").
            if hasattr(sig, "__set_name__"):
                sig.__set_name__(cls, signal_name)

        def make_getter(priv_name, default):
            def getter(self):
                return getattr(self, priv_name, default)
            return getter

        # Collect observer callbacks for this specific property
        prop_observers = observers.get(attr_name, {"watchers": [], "effects": []})
        prop_watchers = list(prop_observers["watchers"])
        prop_effects = list(prop_observers["effects"])

        def make_setter(priv_name, sig_name, prop_name, watchers, effects):
            def setter(self, value):
                old_value = getattr(self, priv_name, _UNSET)
                if old_value is _UNSET:
                    # this is the first __init__ assignment.
                    # don't fire watchers/effects, and suppres notify signal
                    setattr(self, priv_name, value)
                    return
                # if same value, then don't emit signal
                if old_value == value:
                    # No change. Prevent C++ WriteProperty from double-firing.
                    self.__dict__['_qtbridge_suppress_notify'] = True
                    return
                setattr(self, priv_name, value)

                # Invoke @watch callbacks: method(self, change: Change)
                for watcher in watchers:
                    try:
                        watcher(self, Change(name=prop_name, old=old_value, new=value, owner=self))
                    except Exception:
                        _logger.exception("@watch callback %s failed for %s.%s",
                                          getattr(watcher, '__name__', watcher),
                                          cls_name, sig_name)

                # Invoke @effect callbacks: method(self)
                for eff in effects:
                    try:
                        eff(self)
                    except Exception:
                        _logger.exception("@effect callback %s failed for %s.%s",
                                          getattr(eff, '__name__', eff),
                                          cls_name, sig_name)
            return setter

        prop = property(
            fget=make_getter(private_name, default_value),
            fset=make_setter(private_name, signal_name, attr_name, prop_watchers, prop_effects)
        )

        # Set the property on the class
        setattr(cls, attr_name, prop)
        _logger.debug("Created auto_property: %s.%s (default=%r)", cls_name, attr_name, default_value)

    # Mark class as augmented to avoid duplicate processing
    if isinstance(cls, type):
        cls._qtbridge_auto_props_applied = True
    return cls
