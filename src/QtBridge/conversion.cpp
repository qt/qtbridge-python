// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "conversion_p.h"
#include "qtbridgelogging_p.h"

#include <sbkconverter.h>
#include <sbkstring.h>
#include <pysidevariantutils.h>
#include <signalmanager.h>

#include <QtCore/qvariant.h>
#include <QtCore/qmetatype.h>
#include <QtCore/qlist.h>
#include <QtCore/qhash.h>
#include <QtCore/qstring.h>
#include <QtQml/qjsvalue.h>

namespace QtBridges {

std::optional<QString> pyObject2StringOpt(PyObject *obj)
{
    if (!obj || obj == Py_None)
        return std::nullopt;

    if (PyUnicode_Check(obj)) {
        const char *utf8 = Shiboken::String::toCString(obj);
        if (utf8)
            return QString::fromUtf8(utf8);
    }
    return std::nullopt;
}

std::optional<bool> pyObject2BoolOpt(PyObject *obj)
{
    if (!obj || obj == Py_None)
        return std::nullopt;

    if (PyBool_Check(obj))
        return obj == Py_True;

    // Handle truthy/falsy values
    int result = PyObject_IsTrue(obj);
    if (result >= 0)
        return result != 0;

    return std::nullopt;
}

std::optional<QVariant> pyObject2VariantOpt(PyObject *obj)
{
    if (!obj)
        return std::nullopt;

    if (obj == Py_None)
        return {};

    // Handle basic types using Shiboken converters first
    if (PyUnicode_Check(obj)) {
        auto str = pyObject2StringOpt(obj);
        if (str)
            return QVariant(*str);
        return std::nullopt;
    }

    if (PyBool_Check(obj))
        return QVariant(obj == Py_True);

    if (PyLong_Check(obj)) {
        long value = PyLong_AsLong(obj);
        if (!PyErr_Occurred())
            return QVariant(static_cast<int>(value));
        PyErr_Clear();
    }

    if (PyFloat_Check(obj)) {
        double value = PyFloat_AsDouble(obj);
        if (!PyErr_Occurred())
            return QVariant(value);
        PyErr_Clear();
    }

    // Handle lists and tuples
    if (PyList_Check(obj) || PyTuple_Check(obj)) {
        QVariant list = PySide::Variant::convertToVariantList(obj);
        if (list.isValid())
            return list;
        return std::nullopt;
    }

    // Handle dictionaries
    if (PyDict_Check(obj)) {
        QVariant map = PySide::Variant::convertToVariantMap(obj);
        if (map.isValid())
            return map;
        return std::nullopt;
    }

    // Fallback: Wrap Python object in PyObjectWrapper for custom Python classes
    // This follows PySide6's pattern for Sbk objects
    qCDebug(lcQtBridge, "Converting Python object to PyObjectWrapper for QVariant");
    return QVariant::fromValue(PySide::PyObjectWrapper(obj));
}

PyObject *variantList2PyObject(const QVariantList &list)
{
    PyObject *pyList = PyList_New(list.size());
    if (!pyList)
        return nullptr;

    for (int i = 0; i < list.size(); ++i) {
        PyObject *item = variant2PyObject(list[i]);
        if (!item) {
            Py_XDECREF(pyList);
            return nullptr;
        }
        PyList_SetItem(pyList, i, item); // Steals reference
    }

    return pyList;
}

PyObject *variantMap2PyObject(const QVariantMap &map)
{
    PyObject *pyDict = PyDict_New();
    if (!pyDict)
        return nullptr;

    for (auto it = map.constBegin(); it != map.constEnd(); ++it) {
    PyObject *key = Shiboken::String::fromCString(it.key().toUtf8().constData());
        PyObject *value = variant2PyObject(it.value());

        if (!key || !value) {
            Py_XDECREF(key);
            Py_XDECREF(value);
            Py_XDECREF(pyDict);
            return nullptr;
        }

        if (PyDict_SetItem(pyDict, key, value) < 0) {
            Py_XDECREF(key);
            Py_XDECREF(value);
            Py_XDECREF(pyDict);
            return nullptr;
        }

        Py_XDECREF(key);
        Py_XDECREF(value);
    }

    return pyDict;
}

PyObject *variant2PyObject(const QVariant &variant)
{
    if (!variant.isValid())
        Py_RETURN_NONE;

    // Handle complex types first
    switch (variant.typeId()) {
    case QMetaType::QVariantList:
        return variantList2PyObject(variant.toList());
    case QMetaType::QVariantMap:
        return variantMap2PyObject(variant.toMap());
    case QMetaType::QString:
        return Shiboken::String::fromCString(variant.toString().toUtf8().constData());
    case QMetaType::Int:
        return PyLong_FromLong(variant.toInt());
    case QMetaType::Double:
        return PyFloat_FromDouble(variant.toDouble());
    case QMetaType::Bool:
        return PyBool_FromLong(variant.toBool() ? 1 : 0);
    default:
        // Try Shiboken's QVariant converter as fallback
        SbkConverter *converter = Shiboken::Conversions::PrimitiveTypeConverter<QVariant>();
        if (converter) {
            PyObject *result = Shiboken::Conversions::copyToPython(converter, &variant);
            if (result)
                return result;
        }

        qCWarning(lcQtBridge,
              "Unsupported type conversion to Python for: %s",
              variant.metaType().name());
        Py_RETURN_NONE;
    }
}

QVariant convertQVariantQJSValueToQtType(const QVariant &variantWithJSValue)
{

    // Check if this QVariant actually contains a QJSValue
    if (variantWithJSValue.userType() == qMetaTypeId<QJSValue>()) {
        QJSValue jsValue = variantWithJSValue.value<QJSValue>();

        qCDebug(lcQtBridge,
            "Converting QJSValue to Qt type - isArray: %s, isObject: %s, isString: %s, isNumber: %s",
            jsValue.isArray() ? "true" : "false",
            jsValue.isObject() ? "true" : "false",
            jsValue.isString() ? "true" : "false",
            jsValue.isNumber() ? "true" : "false");

        // Handle different QJSValue types explicitly
        // TODO: Expand this as needed for other types
        if (jsValue.isArray()) {
            // For arrays, manually extract elements to ensure proper conversion
            QVariantList list;
            quint32 length = jsValue.property("length").toUInt();

            qCDebug(lcQtBridge, "QJSValue array length: %u", length);

            for (quint32 i = 0; i < length; ++i) {
                QJSValue element = jsValue.property(i);
                QVariant elementVariant = element.toVariant();

                qCDebug(lcQtBridge, "Array element[%u]: %s = %s",
                        i,
                        elementVariant.typeName() ? elementVariant.typeName() : "unknown",
                        elementVariant.toString().toUtf8().constData());

                list.append(elementVariant);
            }

            qCDebug(lcQtBridge,
                "Converted QJSValue array to QVariantList with %lld elements",
                static_cast<long long>(list.size()));
            return QVariant(list);
        }
        else if (jsValue.isObject() && !jsValue.isNull() && !jsValue.isUndefined()) {
            // For objects, convert to QVariantMap
            QVariant converted = jsValue.toVariant();
            qCDebug(lcQtBridge, "Converted QJSValue object to QVariant: %s",
                    converted.typeName() ? converted.typeName() : "unknown");
            return converted;
        }
        else {
            // For primitive values (string, number, bool), use toVariant()
            QVariant converted = jsValue.toVariant();
            qCDebug(lcQtBridge, "Converted QJSValue primitive to QVariant: %s = %s",
                    converted.typeName() ? converted.typeName() : "unknown",
                    converted.toString().toUtf8().constData());
            return converted;
        }
    }

    // If it's not a QJSValue, return as-is
    return variantWithJSValue;
}

// Register conversion functions with Qt's meta-type system
int registerPyObjectMetaTypeConversions()
{
    // Register PyObject* as a meta-type first
    const int result = qRegisterMetaType<PyObject*>();
    Q_UNUSED(result);

    int registeredCount = 0;
    // Register PyObject* -> QVariant conversion
    if (QMetaType::registerConverter<PyObject*, QVariant>(
        [](PyObject* obj) -> QVariant {
            auto result = pyObject2VariantOpt(obj);
            return result ? *result : QVariant();
        }))
        registeredCount++;

    // Register QVariant -> PyObject* conversion
    if (QMetaType::registerConverter<QVariant, PyObject*>(
        [](const QVariant& variant) -> PyObject* {
            return variant2PyObject(variant);
        }))
        registeredCount++;

    // Register QString -> PyObject* conversion
    if (QMetaType::registerConverter<QString, PyObject*>(
        [](const QString& str) -> PyObject* {
            return Shiboken::String::fromCString(str.toUtf8().constData());
        }))
        registeredCount++;

    // Register PyObject* -> QString conversion
    if (QMetaType::registerConverter<PyObject*, QString>(
        [](PyObject* obj) -> QString {
            auto result = pyObject2StringOpt(obj);
            return result ? *result : QString();
        }))
        registeredCount++;

    // Register bool -> PyObject* conversion
    if (QMetaType::registerConverter<bool, PyObject*>(
        [](bool value) -> PyObject* {
            return PyBool_FromLong(value ? 1 : 0);
        }))
        registeredCount++;

    // Register PyObject* -> bool conversion
    if (QMetaType::registerConverter<PyObject*, bool>(
        [](PyObject* obj) -> bool {
            auto result = pyObject2BoolOpt(obj);
            return result ? *result : false;
        }))
        registeredCount++;

    // Register QVariantList -> PyObject* conversion
    if (QMetaType::registerConverter<QVariantList, PyObject*>(
        [](const QVariantList& list) -> PyObject* {
            return variantList2PyObject(list);
        }))
        registeredCount++;

    // Register PyObject* -> QVariantList conversion
    if (QMetaType::registerConverter<PyObject*, QVariantList>(
        [](PyObject* obj) -> QVariantList {
            QVariant result = PySide::Variant::convertToVariantList(obj);
            return result.isValid() ? result.toList() : QVariantList();
        }))
        registeredCount++;

    // Register QVariantMap -> PyObject* conversion
    if (QMetaType::registerConverter<QVariantMap, PyObject*>(
        [](const QVariantMap& map) -> PyObject* {
            return variantMap2PyObject(map);
        }))
        registeredCount++;

    // Register PyObject* -> QVariantMap conversion
    if (QMetaType::registerConverter<PyObject*, QVariantMap>(
        [](PyObject* obj) -> QVariantMap {
            QVariant result = PySide::Variant::convertToVariantMap(obj);
            return result.isValid() ? result.toMap() : QVariantMap();
        }))
        registeredCount++;

    qCDebug(lcQtBridge, "QtBridges: Registered %d PyObject meta-type converters", registeredCount);
    return registeredCount;
}

} // namespace QtBridges
