# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

import os
import sys
from pathlib import Path
from typing import Any


def _setup_dependencies():
    """Ensure Shiboken and PySide6 dependencies are properly loaded."""
    try:
        from shiboken6 import Shiboken  # noqa: F401
    except ImportError:
        paths = ', '.join(sys.path)
        print(
            f"QtBridge/__init__.py: Unable to import Shiboken from {paths}",
            file=sys.stderr
        )
        raise

    try:
        import PySide6  # noqa: F401
    except ImportError:
        paths = ', '.join(sys.path)
        print(
            f"QtBridge/__init__.py: Unable to import PySide6 from {paths}",
            file=sys.stderr
        )
        raise

    if sys.platform == 'win32':
        for dll_dir in [Path(PySide6.__file__).parent, Path(Shiboken.__file__).parent]:
            os.add_dll_directory(str(dll_dir))

# Lazy loading of attributes
def __getattr__(name: str) -> Any:
    if name == "cpython_bridge_instance":
        _setup_dependencies()
        from .QtBridge import bridge_instance
        globals()["cpython_bridge_instance"] = bridge_instance
        return bridge_instance
    if name == "bridge_type":
        _setup_dependencies()
        from .QtBridge import bridge_type
        globals()["bridge_type"] = bridge_type
        return bridge_type
    if name == "insert":
        _setup_dependencies()
        from .QtBridge import insert
        globals()["insert"] = insert
        return insert
    if name == "remove":
        _setup_dependencies()
        from .QtBridge import remove
        globals()["remove"] = remove
        return remove
    if name == "move":
        _setup_dependencies()
        from .QtBridge import move
        globals()["move"] = move
        return move
    if name == "edit":
        _setup_dependencies()
        from .QtBridge import edit
        globals()["edit"] = edit
        return edit
    if name == "reset":
        _setup_dependencies()
        from .QtBridge import reset
        globals()["reset"] = reset
        return reset
    if name == "complete":
        _setup_dependencies()
        from .QtBridge import complete
        globals()["complete"] = complete
        return complete
    if name == "qtbridge":
        _setup_dependencies()
        from .qtbridge_py.qtbridge import qtbridge
        globals()["qtbridge"] = qtbridge
        return qtbridge
    if name == "bridge_instance":
        _setup_dependencies()
        from .qtbridge_py.autoqmlbridge import bridge_instance
        globals()["bridge_instance"] = bridge_instance
        return bridge_instance
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["bridge_instance", "insert", "remove", "move", "edit", "reset", "complete", "qtbridge", "cpython_bridge_instance"]
