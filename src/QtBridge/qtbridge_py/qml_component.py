# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from PySide6.QtCore import QMetaMethod, QMetaObject, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine

try:
    from ._build_config import _logger
except ImportError:
    import logging
    _logger = logging.getLogger("qtbridge-python")


class _MethodInvoker:
    """Callable wrapper around QMetaObject.invokeMethod for a specific method."""

    def __init__(self, qobj, method_name: str):
        self._qobj = qobj
        self._method_name = method_name

    def __call__(self, *args: Any) -> Any:
        result = QMetaObject.invokeMethod(
            self._qobj, self._method_name, Qt.DirectConnection, *args
        )
        return result

    def __repr__(self) -> str:
        return f"<QmlMethod {self._method_name} of {self._qobj}>"


class QmlObject:
    """Python wrapper around a QML created QObject using composition.
    """

    def __init__(self, qobj, component=None):
        # Use object.__setattr__ to bypass our custom __setattr__
        object.__setattr__(self, "_qobj", qobj)
        # Keep the QQmlComponent alive
        object.__setattr__(self, "_component", component)
        # Cache resolved method names so we don't introspect repeatedly
        object.__setattr__(self, "_method_cache", {})

        meta = qobj.metaObject()
        methods: set[str] = set()
        for i in range(meta.methodOffset(), meta.methodCount()):
            method = meta.method(i)
            if method.methodType() in (
                QMetaMethod.MethodType.Method,
                QMetaMethod.MethodType.Slot,
            ):
                name = method.name().data().decode("utf-8")
                methods.add(name)
        object.__setattr__(self, "_methods", methods)

    def __getattr__(self, name: str) -> Any:
        qobj = object.__getattribute__(self, "_qobj")
        methods = object.__getattribute__(self, "_methods")

        # Check if it's a known QML method
        if name in methods:
            cache = object.__getattribute__(self, "_method_cache")
            if name not in cache:
                cache[name] = _MethodInvoker(qobj, name)
            return cache[name]

        # Try signal access: return the PySide6 bound signal directly.
        # PySide6 signals already expose connect(), disconnect(), and emit(),
        # matching the QtBridge.SignalInstance interface.  These are pre-existing
        # signals declared in QML. So this is fine since we don't enable the user
        # to modify them from Python, just connect to them.
        try:
            return getattr(qobj, name)
        except AttributeError:
            pass

        # Fall back to QObject.property() for QML defined Q_PROPERTYs
        meta = qobj.metaObject()
        idx = meta.indexOfProperty(name)
        if idx >= 0:
            return qobj.property(name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        # Underscore-prefixed attributes are stored normally on the wrapper
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        qobj = object.__getattribute__(self, "_qobj")
        meta = qobj.metaObject()
        idx = meta.indexOfProperty(name)
        if idx >= 0:
            if not qobj.setProperty(name, value):
                _logger.warning("setProperty('%s', %r) returned False", name, value)
            return

        # Not a known QML property. Store it on the wrapper itself so that
        # Python only attributes still work.
        object.__setattr__(self, name, value)

    @property
    def qobject(self):
        """Access the underlying QObject directly (escape hatch)."""
        # P.S. ._qobj should also work
        return object.__getattribute__(self, "_qobj")

    def __repr__(self) -> str:
        qobj = object.__getattribute__(self, "_qobj")
        cls = qobj.metaObject().className()
        return f"<QmlObject wrapping {cls}>"


class QmlComponentFactory:
    """Factory for creating instances of a QML component from Python.
    """

    def __init__(self, *, file_path: str | None = None,
                 module: str | None = None, type_name: str | None = None):
        self._file_path = file_path
        self._module = module
        self._type_name = type_name

    def create(self, **initial_properties: Any) -> QmlObject:
        """Create a new instance of the QML component.
        """
        from .qtbridge import get_engine

        engine = get_engine()
        if engine is None:
            raise RuntimeError(
                "No QQmlApplicationEngine is available. "
                "load_qml_component().create() must be called inside a "
                "@qtbridge-decorated function, after the engine has started."
            )

        component = QQmlComponent(engine)

        if self._file_path is not None:
            url = QUrl.fromLocalFile(self._file_path)
            component.loadUrl(url)
        elif self._module is not None and self._type_name is not None:
            component.loadFromModule(self._module, self._type_name)
        else:
            raise RuntimeError(
                "QmlComponentFactory has no valid source. "
                "Provide either a file path or module + type_name."
            )

        if component.isError():
            errors = component.errorString()
            raise RuntimeError(
                f"Failed to load QML component: {errors}"
            )

        if not component.isReady():
            raise RuntimeError(
                f"QML component is not ready (status: {component.status()}). "
                f"Errors: {component.errorString()}"
            )

        if initial_properties:
            obj = component.createWithInitialProperties(initial_properties)
        else:
            obj = component.create()

        if obj is None:
            raise RuntimeError(
                f"QQmlComponent.create() returned None. "
                f"Errors: {component.errorString()}"
            )

        # Prevent the QML engine from garbage-collecting our object
        QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)

        _logger.debug("Created QML object: %s", obj.metaObject().className())
        return QmlObject(obj, component)

    def __repr__(self) -> str:
        if self._file_path:
            return f"<QmlComponentFactory file='{self._file_path}'>"
        return f"<QmlComponentFactory module='{self._module}' type='{self._type_name}'>"


def load_qml_component(
    source: str | None = None,
    *,
    module: str | None = None,
    type_name: str | None = None,
) -> QmlComponentFactory:
    """Load a QML component for instantiation from Python.
    """
    if source is not None:
        # Resolve relative paths against the caller's directory
        path = Path(source)
        if not path.is_absolute():
            caller_frame = inspect.stack()[1]
            caller_dir = Path(caller_frame.filename).resolve().parent
            path = (caller_dir / path).resolve()
        return QmlComponentFactory(file_path=str(path))

    if module is not None and type_name is not None:
        return QmlComponentFactory(module=module, type_name=type_name)

    raise ValueError(
        "load_qml_component() requires either a QML file path as the first "
        "argument, or both 'module' and 'type_name' keyword arguments."
    )
