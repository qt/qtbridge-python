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

try:
    from ._build_config import _logger
except ImportError:
    import logging
    _logger = logging.getLogger("qtbridge-python")

def qtbridge(
    module: str | None = None,
    type_name: str | None = None,
    qml_file: str | None = None,
    import_paths: list[str] | None = None,
):
    """
    Decorator that wraps a function into a QtBridges application context.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger.debug("Starting qtbridge application for function: %s", func.__name__)

            app = QGuiApplication.instance()
            if not app:
                app = QGuiApplication(sys.argv)
            func(*args, **kwargs)
            engine = QQmlApplicationEngine()

            if import_paths:
                for path in import_paths:
                    _logger.debug("Adding QML import path: %s", path)
                    engine.addImportPath(path)
            engine.addImportPath(sys.path[0])

            # --- Load QML content ---
            if qml_file:
                caller_frame = inspect.stack()[1]
                caller_file = Path(caller_frame.filename).resolve().parent

                qml_path = Path(qml_file)
                if not qml_path.is_absolute():
                    qml_path = caller_file / qml_path

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
            del engine
            return result
        return wrapper
    return decorator
