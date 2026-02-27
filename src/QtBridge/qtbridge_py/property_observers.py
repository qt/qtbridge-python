# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

"""
Property observer decorators: ``@watch`` and ``@effect``.

These decorators let you react to auto-property changes entirely on the
Python side.

* ``@watch("prop")`` — called with ``(self, change: Change)`` when the named
  property changes.  *change.old* holds the previous value, *change.new*
  holds the current value.
* ``@effect("prop1", "prop2", ...)`` — called with just ``(self,)``
  whenever *any* of the listed properties change.

"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable

try:
    from ._build_config import _logger
except ImportError:
    import logging
    _logger = logging.getLogger("qtbridge-python")

_WATCH_ATTR = "_qtbridge_watch"
_EFFECT_ATTR = "_qtbridge_effect"


@dataclass
class Change:
    name: str
    old: Any
    new: Any
    owner: Any


def watch(property_name: str) -> Callable:
    """Mark a method as a **watcher** for a single auto-property.
    """

    def decorator(fn: Callable) -> Callable:
        # Validate at decoration time that the method accepts (self, change)
        params = list(inspect.signature(fn).parameters.values())
        positional = [
            p for p in params
            if p.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.POSITIONAL_ONLY,
            )
        ]
        if len(positional) < 2:
            raise TypeError(
                f"@watch-decorated method '{fn.__qualname__}' must accept at least "
                "one parameter in addition to 'self': the 'change: Change' argument."
            )

        existing: list[str] = getattr(fn, _WATCH_ATTR, [])
        existing.append(property_name)
        setattr(fn, _WATCH_ATTR, existing)
        return fn

    return decorator


def effect(*property_names: str) -> Callable:
    """Mark a method as a side-**effect** triggered by one or more properties.
    """

    if not property_names:
        raise TypeError("@effect requires at least one property name")

    def decorator(fn: Callable) -> Callable:
        existing: list[str] = getattr(fn, _EFFECT_ATTR, [])
        existing.extend(property_names)
        setattr(fn, _EFFECT_ATTR, existing)
        return fn

    return decorator

def collect_observers(cls: type) -> dict[str, dict[str, list[Callable]]]:
    """Scan *cls* for methods decorated with ``@watch`` / ``@effect``.

    Returns a mapping::

        {
            "property_name": {
                "watchers": [method, ...],
                "effects":  [method, ...],
            },
            ...
        }
    """
    observers: dict[str, dict[str, list[Callable]]] = {}

    for name in dir(cls):
        try:
            obj = getattr(cls, name)
        except AttributeError:
            continue

        watched_props: list[str] | None = getattr(obj, _WATCH_ATTR, None)
        if watched_props:
            for prop in watched_props:
                observers.setdefault(prop, {"watchers": [], "effects": []})
                observers[prop]["watchers"].append(obj)

        effect_props: list[str] | None = getattr(obj, _EFFECT_ATTR, None)
        if effect_props:
            for prop in effect_props:
                observers.setdefault(prop, {"watchers": [], "effects": []})
                observers[prop]["effects"].append(obj)

    return observers
