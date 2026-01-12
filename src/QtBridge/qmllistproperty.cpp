// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "qmllistproperty_p.h"
#include "qtbridgelogging_p.h"
#include "autoqmlbridgemodel_p.h"
#include "autoqmlbridge_p.h"

#include <autodecref.h>
#include <gilstate.h>
#include <sbkstring.h>
#include <sbkconverter.h>

namespace QtBridges {

PyQmlListProperty::PyQmlListProperty(const PySidePropertyPrivate *original, const char *propertyName)
    : m_propertyName(propertyName ? propertyName : "unknown")
{
    if (original) {
        // Copy all the important attributes from the original property
        typeName = original->typeName;
        pyTypeObject = original->pyTypeObject;
        fget = original->fget;
        fset = original->fset;
        freset = original->freset;
        fdel = original->fdel;
        notify = original->notify;
        getter_doc = original->getter_doc;
        notifySignature = original->notifySignature;
        doc = original->doc;

        // Increment reference counts for Python objects
        Py_XINCREF(pyTypeObject);
        Py_XINCREF(fget);
        Py_XINCREF(fset);
        Py_XINCREF(freset);
        Py_XINCREF(fdel);
        Py_XINCREF(notify);

        qCDebug(lcQtBridge, "Created PyQmlListProperty instance from original property with name: %s",
                m_propertyName);
    } else {
        qCWarning(lcQtBridge, "Created PyQmlListProperty instance with null original");
    }
}

void PyQmlListProperty::metaCall(PyObject *source, QMetaObject::Call call, void **args)
{


    if (call == QMetaObject::ReadProperty) {
        handleReadProperty(source, args);
    } else if (call == QMetaObject::WriteProperty) {
        handleWriteProperty(source, args);
    } else {
        // Fall back to default behavior for other calls
        PySidePropertyPrivate::metaCall(source, call, args);
    }
}

void PyQmlListProperty::handleReadProperty(PyObject *source, void **args)
{
    if (!source || !args) {
        qCWarning(lcQtBridge, "PyQmlListProperty::handleReadProperty: Invalid parameters");
        return;
    }

    Shiboken::GilState gil;

    qCDebug(lcQtBridge, "PyQmlListProperty: Reading list property");

    // Get the Python list using PySidePropertyPrivate::getValue
    // This properly calls the fget with the source object and returns the Python object
    Shiboken::AutoDecRef pyList(getValue(source));

    if (!pyList) {
        qCWarning(lcQtBridge, "PyQmlListProperty: Failed to get value from property");
        return;
    }

    if (!PyList_Check(pyList)) {
        qCWarning(lcQtBridge, "PyQmlListProperty: Property did not return a list");
        return;
    }

    // Get the BridgePyTypeObjectModel owner that wraps this Python object
    BridgePyTypeObjectModel *bridgeModel = nullptr;
    auto it = s_typeModelMap.find(source);
    if (it != s_typeModelMap.end()) {
        bridgeModel = it->second;
        qCDebug(lcQtBridge, "PyQmlListProperty: Found BridgePyTypeObjectModel owner for Python object");
    } else {
        qCWarning(lcQtBridge, "PyQmlListProperty: Could not find BridgePyTypeObjectModel owner for Python object");
        return;
    }

    // Find the property index in the meta-object for change signal emission
    int propertyIndex = -1;
    const char *propertyName = m_propertyName;

    const QMetaObject *metaObj = bridgeModel->metaObject();
    if (m_propertyName && strcmp(m_propertyName, "unknown") != 0) {
        propertyIndex = metaObj->indexOfProperty(propertyName);
        qCDebug(lcQtBridge, "PyQmlListProperty: Found property '%s' at index %d",
                propertyName, propertyIndex);
    } else {
        qCDebug(lcQtBridge, "PyQmlListProperty: No property name available for change signal emission");
    }

    // Create data structure to store both the list and property information
    auto *data = new PyQmlListPropertyData(pyList.object(), bridgeModel, propertyIndex, propertyName);

    // Create QQmlListProperty with the BridgePyTypeObjectModel as the owner
    // We store our data structure as user data instead of just the Python list
    auto *listProperty = new QQmlListProperty<QObject>(
        bridgeModel,  // Use the BridgePyTypeObjectModel directly as the owner
        data,  // Store our data structure
        appendFunction,
        countFunction,
        atFunction,
        clearFunction
    );

    qCDebug(lcQtBridge,
            "PyQmlListProperty: Created QQmlListProperty with %lld items",
            static_cast<long long>(PyList_Size(pyList)));

    // Store the result in the args array
    *reinterpret_cast<QQmlListProperty<QObject>*>(args[0]) = *listProperty;

    // Note: We don't delete listProperty here because Qt takes ownership
    // The Python list reference will be managed by the QQmlListProperty
}

void PyQmlListProperty::handleWriteProperty(PyObject *source, void **args)
{
    // TODO: Check this with the QML team. This is my finding from a few examples.
    // QML typically doesn't directly assign to list properties
    // Instead, it uses the append callback to add items one by one
    qCWarning(lcQtBridge, "PyQmlListProperty: Write property called (unusual for list properties)");

    // If we did need to handle direct assignment, we would:
    // 1. Get the new list from args[0]
    // 2. Convert it to a Python list
    // 3. Call the setter with the new list
    // This is also how we handle normal Python class properties

    // For now, we'll just warn and do nothing
    Q_UNUSED(source);
    Q_UNUSED(args);
}

void PyQmlListProperty::appendFunction(QQmlListProperty<QObject> *property, QObject *value)
{
    if (!property || !property->data || !value) {
        qCWarning(lcQtBridge, "PyQmlListProperty::appendFunction: Invalid parameters");
        return;
    }

    auto *data = static_cast<PyQmlListPropertyData*>(property->data);
    PyObject *pythonList = data->pythonList;

    Shiboken::GilState gil;

    qCDebug(lcQtBridge, "PyQmlListProperty: Appending QObject %p to Python list", value);

    // Extract the Python object from the QObject wrapper using the bridge system
    PyObject *pythonObj = nullptr;

    // Try to get the Python object from AutoQmlBridgeModel
    if (auto *bridgeModel = qobject_cast<AutoQmlBridgeModel*>(value)) {
        pythonObj = bridgeModel->pythonInstance();
    }

    if (!pythonObj) {
        qCWarning(lcQtBridge, "PyQmlListProperty: Could not extract Python object from QObject wrapper");
        return;
    }

    int result = PyList_Append(pythonList, pythonObj);
    if (result != 0) {
        qCWarning(lcQtBridge, "PyQmlListProperty: Failed to append item to Python list");
        PyErr_Clear();
    } else {
        qCDebug(lcQtBridge,
                "PyQmlListProperty: Successfully appended item (list now has %lld items)",
                static_cast<long long>(PyList_Size(pythonList)));

        // Emit property changed signal to notify QML
        emitListPropertyChanged(data);
    }
}

qsizetype PyQmlListProperty::countFunction(QQmlListProperty<QObject> *property)
{
    if (!property || !property->data) {
        qCWarning(lcQtBridge, "PyQmlListProperty::countFunction: Invalid parameters");
        return 0;
    }

    auto *data = static_cast<PyQmlListPropertyData*>(property->data);
    PyObject *pythonList = data->pythonList;

    Shiboken::GilState gil;

    if (!PyList_Check(pythonList)) {
        qCWarning(lcQtBridge, "PyQmlListProperty::countFunction: Data is not a Python list");
        return 0;
    }

    qsizetype count = PyList_Size(pythonList);
    qCDebug(lcQtBridge,
            "PyQmlListProperty: List count requested, returning %lld",
            static_cast<long long>(count));

    return count;
}

QObject *PyQmlListProperty::atFunction(QQmlListProperty<QObject> *property, qsizetype index)
{
    if (!property || !property->data) {
        qCWarning(lcQtBridge, "PyQmlListProperty::atFunction: Invalid parameters");
        return nullptr;
    }

    auto *data = static_cast<PyQmlListPropertyData*>(property->data);
    PyObject *pythonList = data->pythonList;

    Shiboken::GilState gil;

    if (!PyList_Check(pythonList)) {
        qCWarning(lcQtBridge, "PyQmlListProperty::atFunction: Data is not a Python list");
        return nullptr;
    }

    if (index < 0 || index >= PyList_Size(pythonList)) {
        qCWarning(lcQtBridge,
                  "PyQmlListProperty::atFunction: Index %lld out of range",
                  static_cast<long long>(index));
        return nullptr;
    }

    PyObject *item = PyList_GetItem(pythonList, index);
    if (!item) {
        qCWarning(lcQtBridge, "PyQmlListProperty::atFunction: Failed to get item at index %lld",
                  static_cast<long long>(index));
        return nullptr;
    }

    qCDebug(lcQtBridge,
            "PyQmlListProperty: Returning item at index %lld",
            static_cast<long long>(index));

    // Convert Python object back to QObject using the type model map
    // Look up the BridgePyTypeObjectModel wrapper for this Python object in s_typeModelMap
    auto it = s_typeModelMap.find(item);
    if (it != s_typeModelMap.end() && it->second) {
        QObject *qObj = it->second;
        if (qObj) {
            qCDebug(lcQtBridge, "PyQmlListProperty: Found QObject wrapper for Python object");
            return qObj;
        }
    }

    qCWarning(lcQtBridge, "PyQmlListProperty: Could not find QObject wrapper for Python object");
    return nullptr;
}

void PyQmlListProperty::clearFunction(QQmlListProperty<QObject> *property)
{
    if (!property || !property->data) {
        qCWarning(lcQtBridge, "PyQmlListProperty::clearFunction: Invalid parameters");
        return;
    }

    auto *data = static_cast<PyQmlListPropertyData*>(property->data);
    PyObject *pythonList = data->pythonList;

    Shiboken::GilState gil;

    if (!PyList_Check(pythonList)) {
        qCWarning(lcQtBridge, "PyQmlListProperty::clearFunction: Data is not a Python list");
        return;
    }

    qCDebug(lcQtBridge,
            "PyQmlListProperty: Clearing list (had %lld items)",
            static_cast<long long>(PyList_Size(pythonList)));

    // Clear the Python list
    if (PyList_SetSlice(pythonList, 0, PyList_Size(pythonList), nullptr) != 0) {
        qCWarning(lcQtBridge, "PyQmlListProperty: Failed to clear Python list");
        PyErr_Clear();
    } else {
        qCDebug(lcQtBridge, "PyQmlListProperty: Successfully cleared Python list");

        // Emit property changed signal to notify QML
        emitListPropertyChanged(data);
    }
}

void PyQmlListProperty::emitListPropertyChanged(PyQmlListPropertyData *data)
{
    if (!data || !data->owner || data->propertyIndex < 0) {
        qCDebug(lcQtBridge,
            "PyQmlListProperty: Cannot emit property changed signal - missing data (owner: %p, index: %d)",
            data ? data->owner : nullptr,
            data ? data->propertyIndex : -1);
        return;
    }

    qCDebug(lcQtBridge, "PyQmlListProperty: Emitting property changed signal for '%s' at index %d",
            data->propertyName, data->propertyIndex);
    data->owner->emitPropertyChanged(data->propertyIndex);
}

} // namespace QtBridges
