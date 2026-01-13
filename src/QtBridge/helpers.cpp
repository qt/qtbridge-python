// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "helpers_p.h"
#include "qtbridgelogging_p.h"
#include "errorhandler.h"
#include "autoqmlbridgemodel_p.h"
#include "pycapsule_p.h"
#include "qmllistproperty_p.h"

#include <pysideproperty_p.h>
#include <autodecref.h>
#include <sbkstring.h>
#include <gilstate.h>
#include <dynamicqmetaobject.h>
#include <QtCore/qstring.h>
#include <QtQml/qqmllist.h>
#include <QtCore/qobject.h>

namespace QtBridges {

static bool isQmlRegisteredType(PyObject *returnTypeAnnotation, const QByteArray &elementTypeName)
{
    if (!returnTypeAnnotation)
        return false;

    // Get the args tuple from the generic type
    Shiboken::AutoDecRef args(PyObject_GetAttrString(returnTypeAnnotation, "__args__"));
    if (!args.object()) {
        // Clear any error that might have occurred
        PyErr_Clear();
        qCDebug(lcQtBridge, "No __args__ attribute found on type annotation");
        return false;
    }

    if (!PyTuple_Check(args.object())) {
        qCDebug(lcQtBridge, "__args__ is not a tuple");
        return false;
    }

    if (PyTuple_Size(args.object()) < 1) {
        qCDebug(lcQtBridge, "__args__ tuple is empty");
        return false;
    }

    // Get the first argument (the element type)
    PyObject *elementTypeObj = PyTuple_GetItem(args.object(), 0);
    if (!elementTypeObj) {
        qCDebug(lcQtBridge, "Could not get first element from __args__ tuple");
        return false;
    }

    // Check if it's a type object
    if (!PyType_Check(elementTypeObj))
        return false;

    auto *elementType = reinterpret_cast<PyTypeObject*>(elementTypeObj);

    // Check if this type has been registered with QML by looking for stored meta-object
    const QMetaObject *metaObject = getDynamicMetaObjectForType(elementType);

    qCDebug(lcQtBridge, "Checking if type '%s' is QML registered: %s",
            elementTypeName.constData(), metaObject ? "YES" : "NO");

    return metaObject != nullptr;
}

static bool isListTypeHint(const QByteArray &t)
{
    return t.contains("list[") || t.startsWith("typing.List") || t.startsWith("List[");
}

static QByteArray determinePropertyType(PyObject *propertyDescriptor)
{
    if (!propertyDescriptor)
        return "QVariant";

    // Try to get the getter function to examine its return type annotation
    Shiboken::AutoDecRef getter(PyObject_GetAttrString(propertyDescriptor, "fget"));
    if (!getter.object() || getter.object() == Py_None)
        return "QVariant";

    // Get the function's __annotations__ attribute
    Shiboken::AutoDecRef annotations(PyObject_GetAttrString(getter.object(), "__annotations__"));
    if (!annotations.object() || !PyDict_Check(annotations.object()))
        return "QVariant";

    // Look for 'return' annotation
    PyObject *returnType = PyDict_GetItemString(annotations.object(), "return");
    if (!returnType)
        return "QVariant";

    // Check if it's a typing module type
    Shiboken::AutoDecRef typeStr(PyObject_Str(returnType));
    if (!typeStr.object())
        return "QVariant";

    QByteArray typeString = Shiboken::String::toCString(typeStr.object());
    qCDebug(lcQtBridge, "determinePropertyType: typeString from str(): %s",
            typeString.constData());

    // Use specific types only for collections to enable proper QML array/object handling
    if (isListTypeHint(typeString)) {
        // Check if the element type is a registered QML type
        if (isQmlRegisteredType(returnType, typeString)) {
            qCDebug(lcQtBridge, "Detected QML object list property, type: %s",
                    typeString.constData());
            return "QQmlListProperty<QObject>";
        }

        // Fall back to QVariantList for primitive types or unregistered types
        qCDebug(lcQtBridge, "Detected primitive list property, type: %s",
                typeString.constData());
        return "QVariantList";
    }
    if (typeString.contains("dict[") ||
        typeString.startsWith("typing.Dict")) {
        return "QVariantMap";
    }

    // For all primitive types and strings, use QVariant for maximum flexibility
    // This includes: str, int, float, bool, and any other primitive types
    return "QVariant";
}

PySideProperty* createPySidePropertyFromDescriptor(PyObject *classDescriptor,
                                                  PyObject *bindToInstance,
                                                  const char *notifySignature)
{
    if (!classDescriptor || !PyObject_TypeCheck(classDescriptor, &PyProperty_Type))
        return nullptr;

    // Create kwargs dictionary for PySideProperty constructor
    Shiboken::AutoDecRef kwds(PyDict_New());
    if (!kwds)
        return nullptr;

    // Get getter/setter from the property descriptor
    Shiboken::AutoDecRef getter(PyObject_GetAttrString(classDescriptor, "fget"));
    Shiboken::AutoDecRef setter(PyObject_GetAttrString(classDescriptor, "fset"));

    // If we have an instance to bind to, create bound methods
    if (bindToInstance) {
        if (!getter.isNull() && getter.object() != Py_None) {
            Shiboken::AutoDecRef boundGetter(PyObject_CallMethod(
                getter.object(), "__get__", "OO", bindToInstance, Py_None));

            if (PyErr_Occurred()) {
                logPythonException("helpers.cpp: error calling getter.__get__");
                return nullptr;
            }

            if (boundGetter)
                PyDict_SetItemString(kwds.object(), "fget", boundGetter.object());
        }

        if (!setter.isNull() && setter.object() != Py_None) {
            Shiboken::AutoDecRef boundSetter(PyObject_CallMethod(
                setter.object(), "__get__", "OO", bindToInstance, Py_None));

            if (PyErr_Occurred()) {
                logPythonException("helpers.cpp: error calling setter.__get__");
                return nullptr;
            }

            if (boundSetter)
                PyDict_SetItemString(kwds.object(), "fset", boundSetter.object());
        }
    } else {
        // Use unbound getter/setter for type-mode properties
        if (!getter.isNull() && getter.object() != Py_None)
            PyDict_SetItemString(kwds.object(), "fget", getter.object());
        if (!setter.isNull() && setter.object() != Py_None)
            PyDict_SetItemString(kwds.object(), "fset", setter.object());
    }

    // Determine the correct property type from annotations
    QByteArray propertyType = determinePropertyType(classDescriptor);
    PyDict_SetItemString(kwds.object(), "type", PyUnicode_FromString(propertyType.constData()));

    // Get property name
    const char *propName = "<unknown>";
    if (!getter.isNull() && getter.object() != Py_None) {
        Shiboken::AutoDecRef nameAttr(PyObject_GetAttrString(getter.object(), "__name__"));
        if (nameAttr && PyUnicode_Check(nameAttr)) {
            propName = Shiboken::String::toCString(nameAttr);
        }
    }

    // Add notify signal signature if provided
    if (notifySignature)
        PyDict_SetItemString(kwds.object(), "notify",
            PyUnicode_FromString(notifySignature));

    // Create PySideProperty
    PyObject *args = PyTuple_New(0);
    Shiboken::AutoDecRef pysidePropObj(
        PyObject_Call(reinterpret_cast<PyObject *>(PySideProperty_TypeF()),
              args,
              kwds.object()));
    Py_XDECREF(args);

    if (!pysidePropObj)
        return nullptr;

    auto *property = reinterpret_cast<PySideProperty *>(pysidePropObj.object());
    if (!property || !property->d)
        return nullptr;

    // Check if this is a QQmlListProperty and use custom handler
    if (propertyType == "QQmlListProperty<QObject>") {
        // Replace the default property private with our custom list property handler
        // but first copy all the original property data
        PySidePropertyPrivate *originalProperty = property->d;
        property->d = new PyQmlListProperty(originalProperty, propName);
        delete originalProperty;

        qCDebug(lcQtBridge, "Created custom PyQmlListProperty for %s", propName);
    } else {
        // Set up the property data with the determined type (for non-list properties)
        property->d->typeName = propertyType;
        if (!getter.isNull() && getter.object() != Py_None) {
            property->d->fget = getter.object();
            Py_XINCREF(getter.object());
        }
        if (!setter.isNull() && setter.object() != Py_None) {
            property->d->fset = setter.object();
            Py_XINCREF(setter.object());
        }
    }

    // Return the property (caller takes ownership)
    Py_XINCREF(property);
    return property;
}



PySideProperty* registerSingleProperty(const QByteArray &propertyName,
                                     PyObject *classDescriptor,
                                     PyObject *bindToInstance,
                                     PySide::MetaObjectBuilder *metaObjectBuilder,
                                     AutoQmlBridgeModel *model)
{
    if (!classDescriptor || !PyObject_TypeCheck(classDescriptor, &PyProperty_Type) || !metaObjectBuilder) {
        if (!metaObjectBuilder) {
            qCWarning(lcQtBridge,
                      "registerSingleProperty called without metaObjectBuilder - use associateExistingProperty "
                      "for type mode");
        }
        return nullptr;
    }

    QByteArray signalName = propertyName + "Changed";
    int signalId = metaObjectBuilder->addSignal(signalName + "()");

    PySideProperty *property = nullptr;
    if (signalId >= 0) {
        // Construct signal signature directly instead of calling update()
        QByteArray signalSignature = signalName + "()";

        // Create PySideProperty using the optimized signature-based version
        property = createPySidePropertyFromDescriptor(
            classDescriptor, bindToInstance, signalSignature.constData());

        qCDebug(lcQtBridge, "Added notify signal %s for property %s",
                signalName.constData(), propertyName.constData());
    } else {
        qCWarning(lcQtBridge, "Failed to add notify signal %s for property %s",
                   signalName.constData(), propertyName.constData());
        // Fallback if signal creation failed
        property = createPySidePropertyFromDescriptor(
            classDescriptor, bindToInstance, static_cast<const char*>(nullptr));
    }

    if (!property)
        return nullptr;

    // Add property to meta-object builder
    auto *pysidePropObj = reinterpret_cast<PyObject *>(property);
    int propertyIndex = metaObjectBuilder->addProperty(propertyName.constData(), pysidePropObj);

    // Add to model if it exists
    if (model)
        model->addProperty(propertyIndex, property);

    qCDebug(lcQtBridge, "Registered property %s with notify signal",
            propertyName.constData());

    return property;
}

void associateExistingProperty(const QByteArray &propertyName,
                               PyObject *classDescriptor,
                               [[maybe_unused]] PyObject *bindToInstance,
                               AutoQmlBridgeModel *model)
{
    if (!classDescriptor || !PyObject_TypeCheck(classDescriptor, &PyProperty_Type) || !model)
        return;

    // Create a temporary PySideProperty from the descriptor, WITHOUT notify signal.
    // Major TODO:
    // This PySideProperty is only used for property get/set access in qt_metacall().
    // For emitting the notify signal (propertyChanged), we fetch the property from
    // metaObject(), which has the correct notify signal associated (added during bridge_type()).
    // Ideally, only one property creation should happen, and when creating a QML type,
    // we should use a map to pick up the property from the metaObject that was already created.
    // See branch 'refactoring_property_handling' in shyampc for a more robust solution
    // (pending fixes to some errors, but this can come later).
    // NOTE: We pass nullptr here because the instance (m_backend) is passed later
    // in qt_metacall() via property->d->metaCall(m_backend, ...), which binds it there
    PySideProperty *pySideProp = createPySidePropertyFromDescriptor(
        classDescriptor, nullptr, nullptr);
    if (!pySideProp)
        return;

    // Find the property index from the meta-object and associate it
    const QMetaObject *metaObj = model->metaObject();
    if (metaObj) {
        for (int i = metaObj->propertyOffset(); i < metaObj->propertyCount(); ++i) {
            QMetaProperty prop = metaObj->property(i);
            if (prop.name() == propertyName) {
                // Associate the PySideProperty with the model for this index
                model->addProperty(i, pySideProp);
                qCDebug(lcQtBridge,
                        "Associated PySideProperty (no notify) for %s at index %d",
                        propertyName.constData(), i);
                break;
            }
        }
    }
}

PyObject* getDataMethodReturnTypeHint(PyObject *backend)
{
    if (!backend)
        return nullptr;
    Shiboken::GilState gil;
    Shiboken::AutoDecRef dataMethod(PyObject_GetAttrString(backend, "data"));
    if (!dataMethod)
        return nullptr;
    Shiboken::AutoDecRef annotations(PyObject_GetAttrString(dataMethod.object(), "__annotations__"));
    if (!annotations)
        return nullptr;
    PyObject *retType = PyDict_GetItemString(annotations.object(), "return");
    Py_XINCREF(retType); // Return a new reference
    return retType;
}

DataType inferDataType(PyObject *instance)
{
    if (!instance)
        return DataType::Unknown;

    // Check if the data() method exists before attempting to use it
    Shiboken::AutoDecRef hasDataMethod(PyObject_GetAttrString(instance, "data"));
    if (!hasDataMethod.object() || !PyCallable_Check(hasDataMethod.object())) {
        // No data() method or it's not callable - this is fine for non-model types
        PyErr_Clear();
        qCDebug(lcQtBridge, "inferDataType: No callable data() method found. "
                "Returning DataType::Unknown (this is expected for non-model types)");
        return DataType::Unknown;
    }

    // First, try to get type hint from the data() method's return annotation using shared helper
    Shiboken::AutoDecRef returnType(getDataMethodReturnTypeHint(instance));
    if (returnType.object()) {
        Shiboken::AutoDecRef typeStr(PyObject_Str(returnType.object()));
        if (typeStr.object()) {
            QByteArray typeString = Shiboken::String::toCString(typeStr.object());
            qCDebug(lcQtBridge, "inferDataType: Found return type hint: %s",
                    typeString.constData());

            // Check for List[DataClass] pattern
            if (isListTypeHint(typeString) &&
                !typeString.contains("str") &&
                !typeString.contains("int") &&
                !typeString.contains("float")) {
                qCDebug(lcQtBridge,
                        "inferDataType: Type hint suggests DataClassList");

                // Try to verify by checking the actual data
                Shiboken::AutoDecRef dataResult(
                    PyObject_CallMethod(instance, "data", nullptr));
                if (dataResult.object() && !PyErr_Occurred()) {
                    if (isDataClassList(dataResult.object())) {
                        return DataType::DataClassList;
                    }
                }
                PyErr_Clear(); // Clear any error from verification

                // Even if verification failed, trust the type hint
                return DataType::DataClassList;
            }

            // Check for list of primitive types or plain List
            if (isListTypeHint(typeString) || typeString == "list") {
                qCDebug(lcQtBridge, "inferDataType: Type hint suggests List");
                return DataType::List;
            }
        }
    }

    // Fallback: Call the data() method to see what it returns
    Shiboken::AutoDecRef dataResult(PyObject_CallMethod(instance, "data", nullptr));

    if (PyErr_Occurred()) {
        logPythonException("helpers.cpp: error calling instance.data() in inferDataType");
        return DataType::Unknown;
    }

    if (!dataResult.object()) {
        PyErr_Clear();
        return DataType::Unknown;
    }

    PyObject *data = dataResult.object();

    // Check for list or tuple (most common case)
    if (PyList_Check(data) || PyTuple_Check(data)) {
        // Check if it's a list of dataclass objects
        if (isDataClassList(data))
            return DataType::DataClassList;
        return DataType::List;
    }

    // Check for pandas DataFrame (if pandas is available)
    // We check for the type name since we don't want to import pandas just for this
    // TODO: This is not implemented yet
    PyObject *dataType = PyObject_Type(data);
    if (dataType) {
        Shiboken::AutoDecRef typeName(PyObject_GetAttrString(dataType, "__name__"));
        if (typeName.object() && PyUnicode_Check(typeName.object())) {
            if (PyUnicode_CompareWithASCIIString(typeName.object(), "DataFrame") == 0)
                return DataType::Table;
        }
        Py_XDECREF(dataType);
    }

    // If it's some other sequence-like object, treat it as a list
    if (PySequence_Check(data) && !PyUnicode_Check(data))
        return DataType::List;

    // Unknown or unsupported type
    return DataType::Unknown;
}

bool isDataClassInstance(PyObject *obj)
{
    if (!obj || obj == Py_None)
        return false;

    // Check if object has __dataclass_fields__ attribute (standard dataclass marker)
    PyObject *dataclassFields = PyObject_GetAttrString(obj, "__dataclass_fields__");
    if (dataclassFields) {
        Py_XDECREF(dataclassFields);
        return true;
    }

    // Clear the AttributeError that was set by PyObject_GetAttrString
    PyErr_Clear();
    return false;
}

QStringList getDataClassFieldNames(PyObject *dataclassType)
{
    QStringList fieldNames;

    if (!dataclassType)
        return fieldNames;

    // Get __dataclass_fields__ from the type or instance
    PyObject *dataclassFields = PyObject_GetAttrString(dataclassType, "__dataclass_fields__");
    if (!dataclassFields) {
        PyErr_Clear();
        return fieldNames;
    }

    // __dataclass_fields__ is a dict mapping field names to Field objects
    if (PyDict_Check(dataclassFields)) {
        PyObject *keys = PyDict_Keys(dataclassFields);
        if (keys) {
            Py_ssize_t numFields = PyList_Size(keys);
            for (Py_ssize_t i = 0; i < numFields; ++i) {
                PyObject *fieldNameObj = PyList_GetItem(keys, i);
                if (PyUnicode_Check(fieldNameObj)) {
                    const char *fieldName = Shiboken::String::toCString(fieldNameObj);
                    if (fieldName)
                        fieldNames.append(QString::fromUtf8(fieldName));
                }
            }
            Py_XDECREF(keys);
        }
    }

    Py_XDECREF(dataclassFields);
    return fieldNames;
}

// TODO: this needs to be improved. There can ofcourse be an empty dataclass.
bool isDataClassList(PyObject *listObj)
{
    if (!listObj || (!PyList_Check(listObj) && !PyTuple_Check(listObj)))
        return false;

    // Check if the list is non-empty and examine the first item
    Py_ssize_t listSize = PyList_Check(listObj) ? PyList_Size(listObj) : PyTuple_Size(listObj);
    if (listSize == 0)
        return false; // Empty list, assume not dataclass

    PyObject *firstItem = PyList_Check(listObj) ?
                         PyList_GetItem(listObj, 0) :
                         PyTuple_GetItem(listObj, 0);

    return isDataClassInstance(firstItem);
}

} // namespace QtBridges
