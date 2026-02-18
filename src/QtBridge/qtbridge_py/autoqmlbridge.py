# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from __future__ import annotations

from PySide6.QtCore import QRangeModel
from PySide6.QtQml import qmlRegisterSingletonInstance

from .auto_property import augment_class_with_auto_properties

_bridge_map = {}


def bridge_type(type, uri="backend", version="1.0", name=None, default_property=None,
               auto_properties=True, exclude_properties=None):
    if auto_properties and not hasattr(type, '_qtbridge_auto_props_applied'):
        augment_class_with_auto_properties(type, exclude=exclude_properties)

    # selective import
    from QtBridge import cpython_bridge_type

    kwargs = {"uri": uri, "version": version}
    if name is not None:
        kwargs["name"] = name
    if default_property is not None:
        kwargs["default_property"] = default_property
    cpython_bridge_type(type, **kwargs)


def bridge_instance(obj, name, uri="backend", auto_properties=True, exclude_properties=None):
    # Handle numpy arrays
    if "numpy" in type(obj).__module__:
        obj = obj.tolist()

    if isinstance(obj, (list, tuple)):
        model_instance = QRangeModel(obj)
        qmlRegisterSingletonInstance(
            type(model_instance), uri, 1, 0, name, model_instance)
        _bridge_map["model"] = model_instance

    elif hasattr(obj, "__class__"):
        if auto_properties:
            obj_class = type(obj)

            # Only augment if not already done (check for marker attribute)
            if not hasattr(obj_class, '_qtbridge_auto_props_applied'):
                augment_class_with_auto_properties(obj_class, exclude=exclude_properties)

            # Migrate existing plain instance attributes to their auto-property backing
            # fields. This is necessary when the object was instantiated before
            # auto properties were applied, and the __init__ assigned to plain attributes.
            for attr_name in list(obj.__dict__):
                if not attr_name.startswith('_'):
                    descriptor = getattr(type(obj), attr_name, None)
                    if isinstance(descriptor, property):
                        # internally stored with private_name. see auto_property.py
                        private_name = f'_{attr_name}'
                        obj.__dict__[private_name] = obj.__dict__.pop(attr_name)
                        _logger.debug("Migrated instance attr '%s' -> '%s' for %s",
                                      attr_name, private_name, type(obj).__name__)

        from QtBridge import cpython_bridge_instance
        cpython_bridge_instance(obj, name=name, uri=uri)

    else:
        raise TypeError(
            f"Unsupported type for bridge_instance: {type(obj).__name__}"
        )
