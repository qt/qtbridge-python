# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from __future__ import annotations

import sys
import inspect
from functools import wraps
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .qml_component import QmlObject

try:
    from ._build_config import _logger
except ImportError:
    import logging
    _logger = logging.getLogger("qtbridge-python")

# module level variable to hold QML engine
# used for QML component factories
_engine: QQmlApplicationEngine | None = None

# Keeps QML-created objects alive on PySide6 < 6.11, where create() does not
# transfer Python ownership.  Populated by the return value of the user's
# @qtbridge main() function; cleared when the engine shuts down.
# TODO: Remove this when PySide6 6.11+ is the minimum supported version
_keep_alive: list = []


def get_engine() -> QQmlApplicationEngine | None:
    """Return the QQmlApplicationEngine created by the active @qtbridge context,
    or None if no engine is currently running."""
    return _engine

def qtbridge(
    *,
    module: str | None = None,
    type_name: str | None = None,
    qml_file: str | None = None,
    import_paths: list[str] | None = None,
):
    """
    Decorator that wraps a function into a QtBridges application context.
    """
    def decorator(func):
        # Detect whether the user's function wants the root window as an argument.
        _func_params = inspect.signature(func).parameters
        _wants_window = len(_func_params) > 0

        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger.debug("Starting qtbridge application for function: %s", func.__name__)

            # Resolve caller location early so import_paths and qml_file can be
            # interpreted relative to the *script* rather than the CWD.
            caller_frame = inspect.stack()[1]
            caller_dir = Path(caller_frame.filename).resolve().parent

            app = QGuiApplication.instance()
            if not app:
                app = QGuiApplication(sys.argv)

            engine = QQmlApplicationEngine()

            global _engine
            _engine = engine

            if import_paths:
                for path in import_paths:
                    resolved = Path(path)
                    if not resolved.is_absolute():
                        resolved = (caller_dir / resolved).resolve()
                    _logger.debug("Adding QML import path: %s", resolved)
                    engine.addImportPath(str(resolved))
            # Always add the script's own directory so sibling qmldirs are found.
            engine.addImportPath(str(caller_dir))

            if not _wants_window:
                # Standard case: call func() before load so bridge_instance/bridge_type
                # registrations happen before the QML engine starts.
                ret = func(*args, **kwargs)
                if ret is not None:
                    _keep_alive.append(ret)
            else:
                # Window case: func wants the root window, so defer the call until
                # after engine.load() via objectCreated.

                # Import QQuickItem here so Shiboken registers its QVariant converters
                try:
                    from PySide6.QtQuick import QQuickItem  # noqa: F401
                except ImportError:
                    pass  # QtQuick not available — user will get a runtime error if they use it

                def _dispatch(root_obj, _url, _engine=engine, _func=func, _a=args, _kw=kwargs):
                    if root_obj is None:
                        return
                    root_objects = _engine.rootObjects()
                    if not root_objects:
                        return
                    # Wrap the root window in QmlObject so the user can access
                    # properties directly (e.g. window.contentItem, window.width)
                    window = QmlObject(root_objects[0])
                    ret = _func(window, *_a, **_kw)
                    if ret is not None:
                        _keep_alive.append(ret)

                engine.objectCreated.connect(_dispatch)

            # --- Load QML content ---
            if qml_file:
                qml_path = Path(qml_file)
                if not qml_path.is_absolute():
                    qml_path = caller_dir / qml_path

                _logger.debug("Loading QML file: %s", qml_path)
                engine.load(QUrl.fromLocalFile(str(qml_path)))

            elif module and type_name:
                _logger.debug("Loading QML module: %s, type: %s", module, type_name)
                engine.loadFromModule(module, type_name)
            elif module:
                _logger.debug("Loading QML module: %s", module)
                engine.loadFromModule('.', module)
            else:
                raise ValueError("Either 'qml_file' or 'module' must be specified.")

            if not engine.rootObjects():
                _logger.error("No root QML objects loaded, exiting")
                del engine
                sys.exit(-1)

            _logger.debug("Entering event loop")
            result = app.exec()
            _logger.debug("Event loop exited with code: %s", result)
            _engine = None
            _keep_alive.clear()
            del engine
            return result
        return wrapper
    return decorator
