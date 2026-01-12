// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef helpers_P_H
#define helpers_P_H

#include <sbkpython.h>
#include <QtCore/qbytearray.h>
#include <QtCore/qmetaobject.h>

QT_FORWARD_DECLARE_STRUCT(PySideProperty)
QT_FORWARD_DECLARE_CLASS(QMetaMethod)

// Forward declare DataType from autoqmlbridgemodel_p.h
namespace QtBridges {
    enum class DataType;
}

namespace PySide {
class MetaObjectBuilder;
}

namespace QtBridges {

class AutoQmlBridgeModel;

/**
 * Helper function to create a PySideProperty from a Python property descriptor.
 */
PySideProperty* createPySidePropertyFromDescriptor(PyObject *classDescriptor,
                                                  PyObject *bindToInstance = nullptr,
                                                  const char *notifySignature = nullptr);

/**
 * Helper function to register a single property from a Python property descriptor.
 */
PySideProperty* registerSingleProperty(const QByteArray &propertyName,
                                     PyObject *classDescriptor,
                                     PyObject *bindToInstance,
                                     PySide::MetaObjectBuilder *metaObjectBuilder,
                                     AutoQmlBridgeModel *model);

/**
 * Helper function to associate an existing property from meta-object with a model.
 */
void associateExistingProperty(const QByteArray &propertyName,
                             PyObject *classDescriptor,
                             PyObject *bindToInstance,
                             AutoQmlBridgeModel *model);

/**
 * Infer the DataType by calling the data() method and examining its return type.
 * Returns DataType::List for lists/tuples, DataType::DataClassList for lists of dataclass objects,
 * DataType::Table for pandas DataFrames, etc.
 */
DataType inferDataType(PyObject *instance);

/**
 * Check if an object is a dataclass instance
 */
bool isDataClassInstance(PyObject *obj);

/**
 * Extract field names from a dataclass type
 */
QStringList getDataClassFieldNames(PyObject *dataclassType);

/**
 * Check if a list contains dataclass instances
 */
bool isDataClassList(PyObject *listObj);

/**
 * Helper to extract the return type hint of a method named 'data' on a backend object.
 * Returns a new reference to the type hint object, or nullptr if not found.
 */
PyObject* getDataMethodReturnTypeHint(PyObject *backend);
} // namespace QtBridges

#endif // helpers_P_H
