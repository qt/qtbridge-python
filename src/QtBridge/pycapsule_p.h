// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef PYCAPSULE_P_H
#define PYCAPSULE_P_H

#include <sbkpython.h>
#include <QtCore/qtconfigmacros.h>

QT_FORWARD_DECLARE_STRUCT(QMetaObject);

namespace QtBridges {

class AutoQmlBridgePrivate;

#define METAOBJECT_CAPSULE_ATTR "_qtbridges_metaobject"
#define BRIDGE_PRIVATE_CAPSULE_ATTR "_qtbridges_handler"

// QMetaObject storage functions
/**
 * Get dynamic meta object for a Python type (persistent lookup via PyCapsule)
 */
const QMetaObject* getDynamicMetaObjectForType(PyTypeObject* pythonType);

/**
 * Store Python type -> meta object mapping permanently via PyCapsule
 */
void storeDynamicMetaObjectForType(PyTypeObject* pythonType, const QMetaObject* metaObject);

// AutoQmlBridgePrivate storage functions
/**
 * Get AutoQmlBridgePrivate for a Python type (persistent lookup via PyCapsule)
 */
AutoQmlBridgePrivate* getAutoQmlBridgePrivateForType(PyTypeObject* pythonType);

/**
 * Store Python type -> AutoQmlBridgePrivate mapping permanently via PyCapsule
 */
void storeAutoQmlBridgePrivateForType(PyTypeObject* pythonType, AutoQmlBridgePrivate* bridge);

} // namespace QtBridges

#endif // PYCAPSULE_P_H
