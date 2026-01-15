# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import sys
from pathlib import Path


def pytest_configure():
    # Find the built extension
    root_dir = Path(__file__).parent.parent
    # Update pattern to match actual path structure
    build_dir = next(root_dir.glob("build/*/src/QtBridge"), None)
    qtbridge_dir = root_dir / "src" / "QtBridge"
    if build_dir:
        # Add the QtBridges directory directly to sys.path
        sys.path.insert(0, str(build_dir))
        sys.path.insert(0, str(qtbridge_dir))
