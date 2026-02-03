# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import sys
import platform
from pathlib import Path


def pytest_configure():
    # Find the built extension
    root_dir = Path(__file__).parent.parent
    qtbridge_dir = root_dir / "src" / "QtBridge"

    build_dir = None

    # On Windows (MSVC), binaries are under Release or Debug subdirectories
    if platform.system() == "Windows":
        build_dir = next(root_dir.glob("build/*/src/QtBridge/Release"), None)
        # Fall back to Debug build
        if not build_dir:
            build_dir = next(root_dir.glob("build/*/src/QtBridge/Debug"), None)
        # Last fallback
        if not build_dir:
            build_dir = next(root_dir.glob("build/*/src/QtBridge"), None)
    else:
        # Linux/macOS: binaries are directly under build/*/src/QtBridge
        build_dir = next(root_dir.glob("build/*/src/QtBridge"), None)

    if build_dir:
        sys.path.insert(0, str(build_dir))
        sys.path.insert(0, str(qtbridge_dir))
    else:
        raise RuntimeError(
            f"QtBridge build directory not found. "
            f"Tried patterns: build/*/src/QtBridge/Release, build/*/src/QtBridge/Debug, build/*/src/QtBridge. "
            f"Please ensure the project is built before running tests."
        )
