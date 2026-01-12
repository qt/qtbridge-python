# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from PySide6.QtCore import QRangeModel
from PySide6.QtQml import qmlRegisterSingletonInstance

_bridge_map = {}


def bridge_instance(obj, name, uri="backend"):

    # Handle numpy arrays
    if "numpy" in type(obj).__module__:
        obj = obj.tolist()

    if isinstance(obj, (list, tuple)):
        model_instance = QRangeModel(obj)
        qmlRegisterSingletonInstance(
            type(model_instance), uri, 1, 0, name, model_instance)
        _bridge_map["model"] = model_instance

    elif hasattr(obj, "__class__"):
        from QtBridge import cpython_bridge_instance
        cpython_bridge_instance(obj, name=name, uri=uri)

    else:
        raise TypeError(
            f"Unsupported type for bridge_instance: {type(obj).__name__}"
        )
