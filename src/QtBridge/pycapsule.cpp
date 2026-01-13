// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "pycapsule_p.h"
#include "autoqmlbridge_p.h"
#include "qtbridgelogging_p.h"

#include <sbkpython.h>
#include <pep384impl.h>
#include <QtCore/qmetaobject.h>

namespace QtBridges {

// PyCapsule destructor for QMetaObject
static void destroyMetaObjectCapsule(PyObject* capsule)
{
    void* ptr = PyCapsule_GetPointer(capsule, METAOBJECT_CAPSULE_ATTR);
    if (ptr)
        qCDebug(lcQtBridge, "PyCapsule destructor called for QMetaObject (not deleted)");
}

// PyCapsule destructor for AutoQmlBridgePrivate
static void destroyBridgePrivateCapsule(PyObject* capsule)
{
    auto *bridge = static_cast<AutoQmlBridgePrivate*>(
        PyCapsule_GetPointer(capsule, BRIDGE_PRIVATE_CAPSULE_ATTR));
    if (bridge) {
        qCDebug(lcQtBridge, "Destroying AutoQmlBridgePrivate via PyCapsule destructor");
        delete bridge;
    }
}

const QMetaObject* getDynamicMetaObjectForType(PyTypeObject* pythonType)
{
    if (!pythonType) return nullptr;

    // Use PepType_GetDict to check only direct attributes, not inherited ones
    PyObject* typeDict = PepType_GetDict(pythonType);
    if (!typeDict) return nullptr;

    PyObject* capsule = PyDict_GetItemString(typeDict, METAOBJECT_CAPSULE_ATTR);
    if (!capsule) {
        return nullptr;
    }

    // Extract QMetaObject* from the capsule
    const auto *metaObject = static_cast<const QMetaObject*>(
        PyCapsule_GetPointer(capsule, METAOBJECT_CAPSULE_ATTR));

    // Note: capsule is a borrowed reference from PyDict_GetItemString, no need to DECREF

    if (PyErr_Occurred()) {
        PyErr_Clear();
        return nullptr;
    }

    return metaObject;
}

void storeDynamicMetaObjectForType(PyTypeObject* pythonType, const QMetaObject* metaObject)
{
    if (!pythonType || !metaObject) return;

    PyObject* capsule = PyCapsule_New(const_cast<QMetaObject*>(metaObject),
                                      METAOBJECT_CAPSULE_ATTR,
                                      destroyMetaObjectCapsule);
    if (!capsule) {
        qCWarning(lcQtBridge, "Failed to create PyCapsule for QMetaObject");
        return;
    }

    // Set the capsule as an attribute on the Python type
    int result = PyObject_SetAttrString(reinterpret_cast<PyObject*>(pythonType),
                                        METAOBJECT_CAPSULE_ATTR,
                                        capsule);
    Py_DECREF(capsule);

    if (result < 0) {
        qCWarning(lcQtBridge, "Failed to set QMetaObject capsule attribute on Python type");
        PyErr_Clear();
    } else {
        qCDebug(lcQtBridge, "Successfully stored QMetaObject as PyCapsule attribute");
    }
}

AutoQmlBridgePrivate* getAutoQmlBridgePrivateForType(PyTypeObject* pythonType)
{
    if (!pythonType) return nullptr;

    // Use PepType_GetDict to check only direct attributes, not inherited ones
    // This prevents inherited classes from appearing as "already registered"
    PyObject* typeDict = PepType_GetDict(pythonType);
    if (!typeDict) return nullptr;

    PyObject* capsule = PyDict_GetItemString(typeDict, BRIDGE_PRIVATE_CAPSULE_ATTR);
    if (!capsule) {
        return nullptr;
    }

    AutoQmlBridgePrivate* bridge = static_cast<AutoQmlBridgePrivate*>(
        PyCapsule_GetPointer(capsule, BRIDGE_PRIVATE_CAPSULE_ATTR));

    // Note: capsule is a borrowed reference from PyDict_GetItemString, no need to DECREF
    return bridge;
}

void storeAutoQmlBridgePrivateForType(PyTypeObject* pythonType, AutoQmlBridgePrivate* bridge)
{
    if (!pythonType || !bridge) return;

    PyObject* capsule = PyCapsule_New(bridge,
                                      BRIDGE_PRIVATE_CAPSULE_ATTR,
                                      destroyBridgePrivateCapsule);
    if (!capsule) {
        qCWarning(lcQtBridge, "Failed to create PyCapsule for AutoQmlBridgePrivate");
        return;
    }

    // Set the capsule as an attribute on the Python type
    int result = PyObject_SetAttrString(reinterpret_cast<PyObject*>(pythonType),
                                        BRIDGE_PRIVATE_CAPSULE_ATTR,
                                        capsule);
    Py_DECREF(capsule);

    if (result < 0) {
        qCWarning(lcQtBridge, "Failed to set AutoQmlBridgePrivate capsule attribute on Python type");
        PyErr_Clear();
    } else {
        qCDebug(lcQtBridge, "Successfully stored AutoQmlBridgePrivate as PyCapsule attribute");
    }
}

} // namespace QtBridges
