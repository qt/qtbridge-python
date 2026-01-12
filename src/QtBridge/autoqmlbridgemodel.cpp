// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "autoqmlbridgemodel_p.h"
#include "pycapsule_p.h"
#include "qtbridgelogging_p.h"
#include "errorhandler.h"
#include "conversion_p.h"
#include "autoqmlbridge_p.h"
#include "helpers_p.h"
#include "updateqmldecorators/updateqmldecorator_p.h"
#include "updateqmldecorators/decoratorhelpers.h"

#include <sbkpython.h>
#include <sbkerrors.h>
#include <basewrapper.h>
#include <bindingmanager.h>
#include <sbkconverter.h>
#include <pysideproperty_p.h>
#include <QtQml/qqmlengine.h>
#include <pysidevariantutils.h>
#include <pysideclassdecorator_p.h>
#include <autodecref.h>
#include <gilstate.h>
#include <signalmanager.h>
#include <sbkstring.h>
#include <pep384impl.h>

#include <QtCore/qdebug.h>
#include <QtQml/qjsvalue.h>

namespace QtBridges {

constexpr const char* DATA_METHOD_NAME = "data";

AutoQmlBridgeModel::AutoQmlBridgeModel(PyObject *backend, const QMetaObject *metaObject,
                                       DataType datatype)
    : m_backend(backend), m_dynamicMetaObject(metaObject), m_datatype(datatype)
{
    if (m_backend) {
        Py_XINCREF(m_backend);
    }


    if (m_datatype == DataType::DataClassList) {
        setupDataClassRoles();
    }
}

// Protected constructor for subclasses that will set m_backend later
AutoQmlBridgeModel::AutoQmlBridgeModel(const QMetaObject *metaObject, DataType datatype)
    : m_backend(nullptr), m_dynamicMetaObject(metaObject), m_datatype(datatype)
{
    // m_backend will be set later by subclass
}

AutoQmlBridgeModel::~AutoQmlBridgeModel()
{
    if (m_backend) {
        if (Py_IsInitialized()) {
            Shiboken::GilState gil;
            Py_XDECREF(m_backend);
        }
        m_backend = nullptr;
    }
}

int AutoQmlBridgeModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    Shiboken::GilState gil;
    if (!m_backend)
        return 0;

    // If DataType is Unknown, it means this type is being used as a model but doesn't have data()
    // This is an error for bridge_type() registered types
    if (m_datatype == DataType::Unknown) {
        // bridge_type scenario
        const BridgePyTypeObjectModel* typeModel = dynamic_cast<const BridgePyTypeObjectModel*>(this);
        if (typeModel) {
            // Get the type name for a better error message
            Shiboken::AutoDecRef typeObj(PyObject_Type(m_backend));
            const char* typeName = typeObj.object() ? reinterpret_cast<PyTypeObject*>(typeObj.object())->tp_name : "Unknown";

            std::string errorMsg = std::string("Type '") + typeName +
                "' is being used as a QML model but does not have a data() method. " +
                "When using bridge_type() registered types as ListView models, you must provide a data() method. " +
                "Please add a data() method with a return type hint, e.g.:\n" +
                "  def data(self) -> list[str]: ...  # For simple lists\n" +
                "  def data(self) -> List[MyDataClass]: ...  # For dataclass lists";

            PyErr_SetString(PyExc_TypeError, errorMsg.c_str());
            logPythonException("AutoQmlBridgeModel::rowCount");

            // Clear the exception. rowCount() can't propagate Python exceptions
            PyErr_Clear();

            return 0;
        }
    }

    switch (m_datatype) {
    case DataType::List:
    case DataType::DataClassList: {
        Shiboken::AutoDecRef data(PyObject_CallMethod(m_backend, "data", nullptr));

        if (PyErr_Occurred()) {
            logPythonException("AutoQmlBridgeModel::rowCount: error calling backend.data()");
            return 0;
        }

        if (!data || !PyList_Check(data.object()))
            return 0;

        return static_cast<int>(PyList_Size(data.object()));
    }
    // case DataType::Table:
    //     // Future: handle pandas DataFrame
    //     break;
    default:
        return 0;
    }
}

int AutoQmlBridgeModel::columnCount(const QModelIndex &parent) const
{
    Q_UNUSED(parent);
    switch (m_datatype) {
    case DataType::List:
        return 1;
    // case DataType::Table:
    //     // Future: return DataFrame column count
    //     break;
    default:
        return 1;
    }
}

QVariant AutoQmlBridgeModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || !m_backend)
        return {};

    // If DataType is Unknown, it means this type is being used as a model but doesn't have data()
    if (m_datatype == DataType::Unknown) {
        const BridgePyTypeObjectModel* typeModel = dynamic_cast<const BridgePyTypeObjectModel*>(this);
        if (typeModel) {
            // Error already logged in rowCount(), just return empty
            return {};
        }
    }

    switch (m_datatype) {
    case DataType::List: {
        if (role != Qt::DisplayRole)
            return {};

        Shiboken::GilState gil;
        Shiboken::AutoDecRef data(PyObject_CallMethod(m_backend, "data", nullptr));

        if (PyErr_Occurred()) {
            logPythonException("AutoQmlBridgeModel::data: error calling backend.data() (List)");
            return {};
        }

        if (!data || !PyList_Check(data.object()))
            return {};

        int row = index.row();
        if (row < 0 || row >= PyList_Size(data.object()))
            return {};

        PyObject *item = PyList_GetItem(data.object(), row);
        if (!item)
            return {};

        if (PyUnicode_Check(item)) {
            const char *utf8 = Shiboken::String::toCString(item);
            if (!utf8)
                return {};
            return QString::fromUtf8(utf8);
        } else if (PyLong_Check(item)) {
            return QVariant(static_cast<int>(PyLong_AsLong(item)));;
        } else if (PyFloat_Check(item)) {
            return QVariant(PyFloat_AsDouble(item));
        } else if (PyBool_Check(item)) {
            return QVariant(item == Py_True);
        } else if (item == Py_None) {
            return {};
        } else {
            // Fallback: convert to string using str()
            Shiboken::AutoDecRef strObj(PyObject_Str(item));
            if (!strObj.isNull() && PyUnicode_Check(strObj.object())) {
                const char *utf8 = Shiboken::String::toCString(strObj.object());
                if (utf8)
                    return QString::fromUtf8(utf8);
            }
        }
        return {};
    }
    case DataType::DataClassList: {
        Shiboken::GilState gil;
        Shiboken::AutoDecRef data(PyObject_CallMethod(m_backend, "data", nullptr));

        if (PyErr_Occurred()) {
            logPythonException(
                "AutoQmlBridgeModel::data: error calling backend.data() (DataClassList)");
            return {};
        }

        if (!data || !PyList_Check(data.object()))
            return {};

        int row = index.row();
        if (row < 0 || row >= PyList_Size(data.object()))
            return {};

        PyObject *dataclassItem = PyList_GetItem(data.object(), row);
        if (!dataclassItem)
            return {};

        // Find the field name for this role
        QByteArray fieldName = m_dataClassRoles.value(role);

        if (fieldName.isEmpty()) {
            // Fallback to display role - return string representation
            if (role == Qt::DisplayRole) {
                Shiboken::AutoDecRef strObj(PyObject_Str(dataclassItem));
                if (!strObj.isNull() && PyUnicode_Check(strObj.object())) {
                    const char *utf8 = Shiboken::String::toCString(strObj.object());
                    if (utf8)
                        return QString::fromUtf8(utf8);
                }
            }
            return {};
        }

        // Get the field value using getattr
        PyObject *fieldValue = PyObject_GetAttrString(dataclassItem, fieldName.constData());
        if (!fieldValue) {
            PyErr_Clear(); // Clear the AttributeError
            return {};
        }

        // Convert the field value to QVariant
        // TODO: Make this better. Use Shiboken conversion if possible/User conversions.h/.cpp
        QVariant result;
        if (PyUnicode_Check(fieldValue)) {
            const char *utf8 = Shiboken::String::toCString(fieldValue);
            if (utf8)
                result = QString::fromUtf8(utf8);
        } else if (PyLong_Check(fieldValue)) {
            result = QVariant(static_cast<int>(PyLong_AsLong(fieldValue)));
        } else if (PyFloat_Check(fieldValue)) {
            result = QVariant(PyFloat_AsDouble(fieldValue));
        } else if (PyBool_Check(fieldValue)) {
            result = QVariant(fieldValue == Py_True);
        } else if (fieldValue == Py_None) {
            result = QVariant();
        } else {
            // Fallback: convert to string
            Shiboken::AutoDecRef strObj(PyObject_Str(fieldValue));
            if (!strObj.isNull() && PyUnicode_Check(strObj.object())) {
                const char *utf8 = Shiboken::String::toCString(strObj.object());
                if (utf8)
                    result = QString::fromUtf8(utf8);
            }
        }

        Py_XDECREF(fieldValue);
        return result;
    }
    default:
        return {};
    }
}

bool AutoQmlBridgeModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    if (!index.isValid() || role != Qt::EditRole)
        return false;
    if (!m_backend)
        return false;
    Shiboken::GilState gil;
    PyObject *pyValue = nullptr;
    if (value.canConvert<PySide::PyObjectWrapper>()) {
        pyValue = value.value<PySide::PyObjectWrapper>(); // can be implicitly converted
    } else {
        PyErr_SetString(PyExc_TypeError, "Unable to convert QVariant to PyObject in setData()");
        return false;
    }
    if (!pyValue)
        return false;
    // Call Python backend's set_item(index, value)
    Shiboken::AutoDecRef result(PyObject_CallMethod(m_backend, "set_item", "iO", index.row(), pyValue));

    if (PyErr_Occurred()) {
        logPythonException("AutoQmlBridgeModel::setData: error calling backend.set_item()");
        return false;
    }

    if (result.isNull()) {
        if (PyErr_Occurred()) {
            logPythonException("AutoQmlBridgeModel::setData: backend.set_item returned nullptr");
        }
        return false;
    }

    emit dataChanged(index, index, {Qt::DisplayRole, Qt::EditRole});
    return true;
}

Qt::ItemFlags AutoQmlBridgeModel::flags(const QModelIndex &index) const
{
    if (!index.isValid())
        return Qt::NoItemFlags;
    return Qt::ItemIsEditable | Qt::ItemIsEnabled | Qt::ItemIsSelectable;
}

QHash<int, QByteArray> AutoQmlBridgeModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    switch (m_datatype) {
    case DataType::List:
        roles[Qt::DisplayRole] = "display";
        break;
    case DataType::DataClassList:
        // Return the cached dataclass roles if available
        if (!m_dataClassRoles.isEmpty()) {
            return m_dataClassRoles;
        }
        // Fallback to display role if roles not set up yet
        roles[Qt::DisplayRole] = "display";
        break;
    // case DataType::Table:
    //     // Future: add roles for DataFrame columns
    //     break;
    default:
        roles[Qt::DisplayRole] = "display";
        break;
    }
    return roles;
}

QModelIndex AutoQmlBridgeModel::parent(const QModelIndex &child) const
{
    Q_UNUSED(child);
    // For a flat model, always return an invalid QModelIndex
    return QModelIndex();
}

QModelIndex AutoQmlBridgeModel::index(int row, int column, const QModelIndex &parent) const
{
    switch (m_datatype) {
    case DataType::List:
    case DataType::DataClassList:
        if (parent.isValid() || column != 0)
            return QModelIndex();
        return createIndex(row, column);
    // case DataType::Table:
    //     // Future: handle DataFrame index creation
    //     break;
    default:
        return QModelIndex();
    }
}

const QMetaObject *AutoQmlBridgeModel::metaObject() const
{
    if (m_dynamicMetaObject) {
        return m_dynamicMetaObject;
    }
    return QAbstractItemModel::metaObject();
}

void AutoQmlBridgeModel::setDynamicMetaObject(const QMetaObject *metaObject)
{
    m_dynamicMetaObject = metaObject;
}

int AutoQmlBridgeModel::qt_metacall(QMetaObject::Call call, int id, void **args)
{
    // Acquire the GIL
    Shiboken::GilState gil;

    // To convert PyObjectWrapper to AutoQmlBridgeModel
    auto convertVariantToModel = [](QVariant *qvariant) -> bool {
        if (!qvariant || !qvariant->isValid()) {
            return false;
        }

        PySide::PyObjectWrapper wrapper = qvariant->value<PySide::PyObjectWrapper>();
        PyObject *pyObj = wrapper;  // Use implicit conversion operator
        if (!pyObj) {
            return false;
        }

        // Check if this Python object has a registered AutoQmlBridgeModel
        auto it = s_bridgeMap.find(pyObj);
        if (it != s_bridgeMap.end()) {
            // Replace the Python object with the C++ AutoQmlBridgeModel
            AutoQmlBridgeModel *cppModel = it->second->model();

            // Explicitly set C++ ownership to prevent Qt/QML from trying to delete this object
            // The model is owned by shared_ptr<AutoQmlBridgePrivate>
            QQmlEngine::setObjectOwnership(cppModel, QQmlEngine::CppOwnership);
            *qvariant = QVariant::fromValue(cppModel);
            qCDebug(lcQtBridge, "Converted PyObjectWrapper to AutoQmlBridgeModel (C++ ownership)");
            return true;
        }
        return false;
    };

    auto base_id = QAbstractItemModel::qt_metacall(call, id, args);
    if (base_id < 0)
        return base_id;

    // for property dealing
    if (call == QMetaObject::ReadProperty || call == QMetaObject::WriteProperty) {
        // Retrieve the PySideProperty from the mapping
        PySideProperty *property = m_propertyMap.value(id, nullptr);
        if (!property) {
            qCDebug(lcQtBridge, "Property not found for id: %d", id);
            return -1;
        }
        if (!property->d) {
            qCDebug(lcQtBridge, "Property private data is null for id: %d", id);
            return -1;
        }

        if (call == QMetaObject::WriteProperty) {
            // QML may pass QVariant containing QJSValue, convert to proper Qt type
            if (args && args[0]) {
                // First, try interpreting as QVariant
                QVariant *variantPtr = reinterpret_cast<QVariant*>(args[0]);
                qCDebug(lcQtBridge, "WriteProperty received QVariant - type: %s, userType: %d",
                        variantPtr->typeName() ? variantPtr->typeName() : "unknown",
                        variantPtr->userType());

                // Check if this QVariant contains a BridgePyTypeObjectModel
                // (from QML instantiated Python types)
                // If it's a BridgePyTypeObjectModel, we need to extract m_backend
                if (variantPtr->canConvert<QObject*>()) {
                    QObject *qobj = variantPtr->value<QObject*>();
                    if (qobj) {
                        // Direct cast: we know the type stored is BridgePyTypeObjectModel*
                        BridgePyTypeObjectModel *model =
                            static_cast<BridgePyTypeObjectModel*>(qobj);
                        if (model && model->m_backend) {
                            qCDebug(lcQtBridge,
                                    "WriteProperty: Converting BridgePyTypeObjectModel* to Python backend object");
                            Shiboken::GilState gil;

                            // Create a QVariant containing the Python object
                            // We'll convert it using PySide's variant converter
                            PyObject *backendObj = model->m_backend;
                            Py_INCREF(backendObj);

                            // Convert Python object to QVariant for PySide
                            auto variantOpt = pyObject2VariantOpt(backendObj);
                            Py_DECREF(backendObj);

                            if (variantOpt.has_value()) {
                                QVariant pythonVariant = variantOpt.value();
                                void *convertedArgs[1] = { &pythonVariant };
                                property->d->metaCall(m_backend, call, convertedArgs);

                                // Emit the notify signal after property write
                                emitPropertyChanged(id);
                                return -1;
                            }
                        }
                    }
                }

                // Check if this QVariant contains a QJSValue and convert if needed
                QVariant converted = convertQVariantQJSValueToQtType(*variantPtr);

                if (converted.userType() != variantPtr->userType()) {
                    qCDebug(lcQtBridge, "Converted QVariant(QJSValue) to %s",
                            converted.typeName() ? converted.typeName() : "unknown");

                    // Create new args array with converted QVariant
                    void *convertedArgs[1] = { &converted };
                    property->d->metaCall(m_backend, call, convertedArgs);

                    // Emit the notify signal after property write
                    emitPropertyChanged(id);
                    return -1;
                }
                // If no conversion was needed, fall through to normal handling
            }
        }

        // Forward the call to PySidePropertyPrivate::metaCall
        property->d->metaCall(m_backend, call, args);

        // For ReadProperty, check if the returned PyObject has an associated AutoQmlBridgeModel
        // If so, replace it with the C++ model for QML
        if (call == QMetaObject::ReadProperty && args[0]) {
            // Check if this is a list property by examining the meta-property type
            // if so, skip the QVariant conversion
            const QMetaObject *mo = metaObject();
            int propertyIndex = id;
            bool isListProperty = false;
            QByteArray typeName;

            if (propertyIndex >= 0 && propertyIndex < mo->propertyCount()) {
                QMetaProperty metaProp = mo->property(propertyIndex);
                typeName = metaProp.typeName();
                // Check if it's a QQmlListProperty - these are NOT passed as QVariant*
                if (typeName.startsWith("QQmlListProperty")) {
                    isListProperty = true;
                    qCDebug(lcQtBridge,
                            "ReadProperty for QQmlListProperty: %s (skipping QVariant conversion)",
                            metaProp.name());
                }
            }

            // Only treat as QVariant if it's NOT a list property
            if (!isListProperty) {
                QVariant *propertyValue = reinterpret_cast<QVariant *>(args[0]);
                if (typeName == "QVariantList" || typeName == "QVariantMap") {
                    // For primitive lists/maps, return the QVariant directly to QML
                    *reinterpret_cast<QVariant *>(args[0]) = *propertyValue;
                    return -1;
                }
                if (propertyValue->canConvert<PySide::PyObjectWrapper>()) {
                    // Check if this is a bridge_type() created object (in s_typeModelMap)
                    // These should be returned as QObject* for QML, not converted to Model
                    PySide::PyObjectWrapper wrapper = propertyValue->value<PySide::PyObjectWrapper>();
                    PyObject *pyObj = wrapper;
                    if (pyObj) {
                        auto typeIt = s_typeModelMap.find(pyObj);
                        if (typeIt != s_typeModelMap.end()) {
                            // This is a QML-instantiated object (bridge_type), return as QObject*
                            BridgePyTypeObjectModel *qmlObj = typeIt->second;
                            *propertyValue = QVariant::fromValue(static_cast<QObject*>(qmlObj));
                            qCDebug(lcQtBridge,
                                    "Converted PyObjectWrapper to QObject* for QML-instantiated type (QObject*=%p)",
                                    qmlObj);
                        } else {
                            // Check if this is in s_bridgeMap (registered via bridge_instance)
                            auto bridgeIt = s_bridgeMap.find(pyObj);
                            if (bridgeIt != s_bridgeMap.end()) {
                                // This is a bridge_instance() object, convert to Model
                                convertVariantToModel(propertyValue);
                                qCDebug(lcQtBridge,
                                        "Converted PyObjectWrapper to AutoQmlBridgeModel for "
                                        "bridge_instance");
                            } else {
                                qCDebug(lcQtBridge,
                                        "ReadProperty: PyObject %p not found in s_typeModelMap or "
                                        "s_bridgeMap, leaving as PyObjectWrapper",
                                        pyObj);
                            }
                        }
                    } else {
                        qCDebug(lcQtBridge,
                                "ReadProperty: PyObjectWrapper is null for property id %d", id);
                    }
                }
            }
        }

        // For WriteProperty, emit the notify signal after the property has been set
        if (call == QMetaObject::WriteProperty) {
            emitPropertyChanged(id);
        }

        return -1;
    }

    if (call == QMetaObject::InvokeMetaMethod) {
        // Get method info
        const QMetaMethod method = m_dynamicMetaObject->method(id);
        const QByteArray methodName = method.name();
        const int paramCount = method.parameterCount();

        // Print method name
        qCDebug(lcQtBridge, "Trying to call Python method: %s", methodName.constData());

        // Fetch the Python method
        Shiboken::AutoDecRef methodNameStr(PyUnicode_FromString(methodName.constData()));
        if (!methodNameStr) {
            logPythonException("qt_metacall: Failed to convert method name to Python string");
            return id;
        }

        Shiboken::AutoDecRef callable(PyObject_GetAttr(m_backend, methodNameStr));
        if (callable.isNull()) {
            qCWarning(lcQtBridge, "Failed to get Python method: %s", methodName.constData());
            logPythonException("qt_metacall: get Python method");
            return id;
        }

        // Create arguments tuple
        Shiboken::AutoDecRef pyArgs(PyTuple_New(paramCount));
        if (!pyArgs) {
            logPythonException("qt_metacall: PyTuple_New");
            return id;
        }

        for (int i = 0; i < paramCount; ++i) {
            const QVariant& arg = *reinterpret_cast<QVariant*>(args[i + 1]);
            QVariant convertedArg = arg;

            if (arg.userType() == qMetaTypeId<QJSValue>())
                convertedArg = convertQVariantQJSValueToQtType(arg);

            PyObject* pyArg = variant2PyObject(convertedArg);
            if (!pyArg) {
                logPythonException("qt_metacall: arg conversion");
                return id;
            }
            PyTuple_SetItem(pyArgs, i, pyArg);
        }

        // Call the Python method
        Shiboken::AutoDecRef result(PyObject_CallObject(callable, pyArgs));
        if (result.isNull()) {
            if (PyErr_Occurred()) {
                Shiboken::Errors::Stash stash;
                logPythonException("qt_metacall: call Python method", stash.getException());
            } else {
                PyErr_SetString(PyExc_RuntimeError, "qt_metacall: Unknown error in Python method");
            }
            return id;
        }

        // Handle return value if method has a non-void return type
        const QByteArray returnTypeName = method.typeName();
        if (returnTypeName != "void" && !returnTypeName.isEmpty() && args[0]) {
            QVariant *returnValue = reinterpret_cast<QVariant*>(args[0]);
            auto variantOpt = pyObject2VariantOpt(result.object());
            if (variantOpt.has_value()) {
                *returnValue = variantOpt.value();
                if (returnValue->canConvert<PySide::PyObjectWrapper>())
                    convertVariantToModel(returnValue);
                qCDebug(lcQtBridge) << "Method" << methodName << "returned:" << *returnValue;
            } else {
                qCWarning(lcQtBridge) << "Failed to convert return value for method" << methodName
                                      << "with return type" << returnTypeName;
            }
        }
    }
    return id;
}

void AutoQmlBridgeModel::addProperty(int propertyIndex, PySideProperty *property)
{
    m_propertyMap[propertyIndex] = property;
}

void AutoQmlBridgeModel::startInsert(int first, int last)
{
    beginInsertRows(QModelIndex(), first, last);
}

void AutoQmlBridgeModel::finishInsert()
{
    endInsertRows();
}

void AutoQmlBridgeModel::startRemove(int first, int last)
{
    beginRemoveRows(QModelIndex(), first, last);
}

void AutoQmlBridgeModel::finishRemove()
{
    endRemoveRows();
}

void AutoQmlBridgeModel::startMove(int sourceFirst, int sourceLast, int destinationRow)
{
    beginMoveRows(QModelIndex(), sourceFirst, sourceLast, QModelIndex(), destinationRow);
}

void AutoQmlBridgeModel::finishMove()
{
    endMoveRows();
}

void AutoQmlBridgeModel::startReset()
{
    beginResetModel();
}

void AutoQmlBridgeModel::endReset()
{
    // If we're dealing with a DataClassList and roles haven't been set up yet,
    // try to set them up now (in case data was empty before but now has items)
    if (m_datatype == DataType::DataClassList && m_dataClassRoles.isEmpty()) {
        // Clear cached field names to force re-inspection
        m_dataClassFieldNames.clear();
        setupDataClassRoles();

        if (!m_dataClassRoles.isEmpty()) {
            qCDebug(lcQtBridge,
                    "AutoQmlBridgeModel::endReset: Set up %lld dataclass roles after reset",
                    static_cast<long long>(m_dataClassRoles.size()));
        }
    }

    endResetModel();
}

// BridgePyTypeObjectModel Implementation

// Constructor for QML factory function with explicit Python type
BridgePyTypeObjectModel::BridgePyTypeObjectModel(QObject *parent, PyTypeObject *pythonType)
    : AutoQmlBridgeModel(nullptr, DataType::Unknown),  // Use protected constructor
      m_pythonType(pythonType)
{
    if (parent != nullptr)
        setParent(parent);

    qCDebug(lcQtBridge,
            "BridgePyTypeObjectModel constructor called with explicit Python type: %s, parent: %p",
            pythonType ? pythonType->tp_name : "null", parent);

    if (m_pythonType) {
        Shiboken::GilState gil;
        Py_XINCREF(m_pythonType);

        // Get the stored dynamic meta object for this Python type
        const QMetaObject *dynamicMeta = QtBridges::getDynamicMetaObjectForType(m_pythonType);
        if (dynamicMeta) {
            // Set the dynamic MetaObject in the constructor - this is crucial for QML registration
            m_dynamicMetaObject = dynamicMeta;
            qCDebug(lcQtBridge, "Set dynamic meta object for Python type: %s (className: %s)",
                    m_pythonType->tp_name, dynamicMeta->className());
        } else {
            qCWarning(lcQtBridge,
                      "No dynamic meta object found for Python type: %s",
                      m_pythonType->tp_name);
            // Fall back to QAbstractItemModel if no dynamic meta object is available
            m_dynamicMetaObject = &QAbstractItemModel::staticMetaObject;
        }

        // Create the Python instance and set m_backend
        createPythonInstance();

        if (m_backend) {
            qCDebug(lcQtBridge,
                    "Created BridgePyTypeObjectModel for Python type: %s with valid Python instance",
                    m_pythonType->tp_name);
        } else {
            qCWarning(lcQtBridge,
                      "Created BridgePyTypeObjectModel for Python type: %s but Python instance creation "
                      "failed",
                      m_pythonType->tp_name);
        }
    } else {
        qCWarning(lcQtBridge, "BridgePyTypeObjectModel created with null Python type!");
        m_dynamicMetaObject = &QAbstractItemModel::staticMetaObject;
    }
}

BridgePyTypeObjectModel::~BridgePyTypeObjectModel()
{
    const char* typeName = (m_pythonType && m_pythonType->tp_name) ? m_pythonType->tp_name : "null";

    // Remove from global type model map before cleanup
    if (m_backend) {
        auto it = s_typeModelMap.find(m_backend);
        if (it != s_typeModelMap.end()) {
            s_typeModelMap.erase(it);
        }
    }

    // Only handle Python references if Python is still initialized
    if (m_pythonType && Py_IsInitialized()) {
        try {
            Shiboken::GilState gil;
            // Store the type name before decrementing reference
            const char* typeNameForLogging = m_pythonType->tp_name;
            Py_XDECREF(m_pythonType);
            qCDebug(lcQtBridge, "Released Python type reference for: %s", typeNameForLogging);
        } catch (...) {
            // Catch any exceptions during Python cleanup to prevent crash
            qCWarning(lcQtBridge, "Exception during Python type cleanup for: %s", typeName);
        }
        m_pythonType = nullptr;  // Prevent accidental reuse
    }
}

void BridgePyTypeObjectModel::createPythonInstance()
{
    if (m_instanceCreated || !m_pythonType)
        return;

    Shiboken::GilState gil;

    try {
        // Call Python type to create instance: MyClass()
        PyObject *instance = PyObject_CallObject(reinterpret_cast<PyObject*>(m_pythonType), nullptr);

        if (!instance) {
            std::string error = "Failed to create Python instance for type: " +
                              std::string(m_pythonType->tp_name);
            logPythonException(error.c_str());
            return;
        }

        // Set the backend instance
        m_backend = instance;

        // PyObject_CallObject already returns a new reference, which is what we want
        // The AutoQmlBridgeModel destructor will Py_XDECREF(m_backend) to match this reference

        // Infer the data type from the instance
        m_datatype = inferDataType(m_backend);
        if (m_datatype == DataType::Unknown) {
            qCDebug(lcQtBridge,
                     "Could not infer data type for Python instance of type: %s. "
                     "This is fine if the type is not used as a QML model. "
                     "If using as a model, add a return type hint to your data() method.",
                     m_pythonType->tp_name);
        } else {
            const char* datatypeName = "Unknown";
            switch (m_datatype) {
                case DataType::List: datatypeName = "List"; break;
                case DataType::DataClassList: datatypeName = "DataClassList"; break;
                case DataType::Table: datatypeName = "Table"; break;
                default: break;
            }
            qCDebug(lcQtBridge, "Inferred data type for %s: %s",
                   m_pythonType->tp_name, datatypeName);
        }

        s_typeModelMap[m_backend] = this;

        m_instanceCreated = true;

        // Bind decorators to this backend instance
        bindDecoratorsToBackend();

        // Now that we have the Python instance, discover and register properties
        // that were registered during bridge_type() but couldn't be added to the model
        discoverAndRegisterProperties();

        qCDebug(lcQtBridge, "Successfully created Python instance for type: %s",
                m_pythonType->tp_name);

    } catch (const std::exception& e) {
        std::string error = "Exception creating Python instance for type " +
                          std::string(m_pythonType->tp_name) + ": " + e.what();
        logPythonException(error.c_str());
    }
}

void BridgePyTypeObjectModel::bindDecoratorsToBackend()
{
    if (!m_pythonType || !m_backend)
        return;

    Shiboken::GilState gil;

    // Use PyObject_Dir to get all attributes including inherited ones, not just direct class dict
    Shiboken::AutoDecRef dirList(PyObject_Dir(reinterpret_cast<PyObject*>(m_pythonType)));
    if (!dirList)
        return;

    const Py_ssize_t count = PyList_Size(dirList.object());
    for (Py_ssize_t i = 0; i < count; ++i) {
        PyObject *nameObj = PyList_GetItem(dirList.object(), i);
        if (!PyUnicode_Check(nameObj))
            continue;

        const char *methodName = Shiboken::String::toCString(nameObj);
        Shiboken::AutoDecRef value(PyObject_GetAttrString(reinterpret_cast<PyObject*>(m_pythonType), methodName));
        if (!value)
            continue;

        // Check if this is one of our decorators
        if (qstrcmp(Py_TYPE(value.object())->tp_name, "QtBridges.insert") == 0 ||
            qstrcmp(Py_TYPE(value.object())->tp_name, "QtBridges.remove") == 0 ||
            qstrcmp(Py_TYPE(value.object())->tp_name, "QtBridges.move") == 0 ||
            qstrcmp(Py_TYPE(value.object())->tp_name, "QtBridges.edit") == 0 ||
            qstrcmp(Py_TYPE(value.object())->tp_name, "QtBridges.reset") == 0 ||
            qstrcmp(Py_TYPE(value.object())->tp_name, "QtBridges.complete") == 0) {
            auto *pData = PySide::ClassDecorator::DecoratorPrivate::get<QtBridges::UpdateQMLDecoratorPrivate>(value.object());
            if (pData) {
                pData->setBackendInstance(m_backend);
                qCDebug(lcQtBridge, "Bound decorator %s to backend instance %p for type %s",
                       methodName, m_backend, m_pythonType->tp_name);
            }
        }
    }
}

void BridgePyTypeObjectModel::discoverAndRegisterProperties()
{
    if (!m_pythonType || !m_backend)
        return;

    Shiboken::GilState gil;

    // Get the meta-object to find properties that were registered during bridge_type()
    const QMetaObject *metaObj = metaObject();
    if (!metaObj)
        return;

    // Iterate through all properties in the meta-object
    for (int i = metaObj->propertyOffset(); i < metaObj->propertyCount(); ++i) {
        QMetaProperty prop = metaObj->property(i);
        QByteArray propName = prop.name();

        // Check if this property exists on the Python type
        Shiboken::AutoDecRef classDescriptor(
            PyObject_GetAttrString(reinterpret_cast<PyObject*>(m_pythonType), propName.constData()));

        if (!classDescriptor || !PyObject_TypeCheck(classDescriptor.object(), &PyProperty_Type))
            continue;

        // Associate the existing property with this model instance
        associateExistingProperty(propName, classDescriptor.object(), m_backend, this);

        qCDebug(lcQtBridge, "Discovered and associated property %s for instance of type %s",
                propName.constData(), m_pythonType->tp_name);
    }
}

void AutoQmlBridgeModel::emitPropertyChanged(int propertyIndex)
{
    const QMetaObject *metaObj = metaObject();
    if (!metaObj || propertyIndex < 0 || propertyIndex >= metaObj->propertyCount()) {
        qCDebug(lcQtBridge) << "emitPropertyChanged: Invalid property index" << propertyIndex;
        return;
    }

    QMetaProperty property = metaObj->property(propertyIndex);
    if (!property.hasNotifySignal()) {
        qCDebug(lcQtBridge) << "emitPropertyChanged: Property" << property.name()
                           << "has no notify signal";
        return;
    }

    QMetaMethod notifySignal = property.notifySignal();
    int methodIndex = notifySignal.methodIndex();
    int signalIndex = methodIndex - metaObj->methodOffset();

    qCDebug(lcQtBridge) << "emitPropertyChanged: Emitting" << notifySignal.name()
                       << "for property" << property.name()
                       << "methodIndex:" << methodIndex
                       << "signalIndex:" << signalIndex
                       << "methodOffset:" << metaObj->methodOffset();

    // Emit the signal using QMetaObject::activate
    QMetaObject::activate(this, metaObj, signalIndex, nullptr);
}

QStringList AutoQmlBridgeModel::getDataClassFieldNames() const
{
    if (!m_dataClassFieldNames.isEmpty()) {
        return m_dataClassFieldNames;
    }

    if ((m_datatype != DataType::DataClassList && m_datatype != DataType::Table) || !m_backend) {
        return {};
    }

    // Use shared helper to get the return type hint of data()
    Shiboken::AutoDecRef returnType(QtBridges::getDataMethodReturnTypeHint(m_backend));
    if (returnType) {
        Shiboken::AutoDecRef args(PyObject_GetAttrString(returnType, "__args__"));
        if (args && PyTuple_Check(args) && PyTuple_Size(args) > 0) {
            PyObject *dataclassType = PyTuple_GetItem(args, 0);
            if (dataclassType && PyType_Check(dataclassType)) {
                // Try to get field names from the dataclass type
                QStringList fieldNames = QtBridges::getDataClassFieldNames(dataclassType);
                if (!fieldNames.isEmpty()) {
                    qCDebug(lcQtBridge,
                            "AutoQmlBridgeModel::getDataClassFieldNames: Got %lld fields from type hint",
                            static_cast<long long>(fieldNames.size()));
                    return fieldNames;
                }
            }
        }
        PyErr_Clear(); // Clear any errors from type hint inspection
    }

    // Fallback: Get the first dataclass instance from the data() method
    Shiboken::AutoDecRef data(PyObject_CallMethod(m_backend, "data", nullptr));

    if (PyErr_Occurred()) {
        logPythonException("AutoQmlBridgeModel::getDataClassFieldNames: error calling backend.data()");
        return {};
    }

    if (!data || !PyList_Check(data.object()) || PyList_Size(data.object()) == 0) {
        qCDebug(lcQtBridge,
                "AutoQmlBridgeModel::getDataClassFieldNames: data() returned empty or non-list");
        return {};
    }

    PyObject *firstItem = PyList_GetItem(data.object(), 0);
    if (!firstItem) {
        return {};
    }

    return QtBridges::getDataClassFieldNames(firstItem);
}

void AutoQmlBridgeModel::setupDataClassRoles()
{
    // Cache field names
    m_dataClassFieldNames = getDataClassFieldNames();

    // Clear existing roles
    m_dataClassRoles.clear();

    // Set up roles starting from a high number to avoid conflicts with Qt built-in roles
    int baseRole = Qt::UserRole + 1000;

    for (int i = 0; i < m_dataClassFieldNames.size(); ++i) {
        const QString &fieldName = m_dataClassFieldNames[i];
        m_dataClassRoles[baseRole + i] = fieldName.toUtf8();
    }

    qCDebug(lcQtBridge, "SetupDataClassRoles: Created %lld roles for dataclass fields",
        static_cast<long long>(m_dataClassRoles.size()));
}

void *BridgePyTypeObjectModel::qt_metacast(const char *classname)
{
    // Handle QQmlParserStatus interface casting manually
    // This replaces the functionality normally provided by Q_INTERFACES(QQmlParserStatus)
    if (qstrcmp(classname, "QQmlParserStatus") == 0) {
        return static_cast<QQmlParserStatus*>(this);
    }

    // For other interfaces, fall back to the parent implementation
    return AutoQmlBridgeModel::qt_metacast(classname);
}

void BridgePyTypeObjectModel::componentComplete()
{
    // Call any @complete decorated methods
    callCompleteDecorators();
}

void BridgePyTypeObjectModel::callCompleteDecorators()
{
    if (!m_pythonType || !m_backend) {
        qCWarning(lcQtBridge,
                "callCompleteDecorators: Missing pythonType (%p) or backend (%p), cannot proceed",
                m_pythonType, m_backend);
        return;
    }

    Shiboken::GilState gil;

    // Use PyObject_Dir() to get all attributes including inherited ones
    Shiboken::AutoDecRef dirList(PyObject_Dir(reinterpret_cast<PyObject*>(m_pythonType)));
    if (!dirList || !PyList_Check(dirList.object())) {
        qCWarning(lcQtBridge, "callCompleteDecorators: Failed to get attribute list from Python type");
        return;
    }

    const Py_ssize_t listSize = PyList_Size(dirList.object());

    for (Py_ssize_t i = 0; i < listSize; ++i) {
        PyObject *key = PyList_GetItem(dirList.object(), i);
        if (!key || !PyUnicode_Check(key))
            continue;

        const char *attrName = Shiboken::String::toCString(key);
        if (!attrName)
            continue;

        // Get the attribute from the type (not the instance)
        Shiboken::AutoDecRef value(PyObject_GetAttrString(reinterpret_cast<PyObject*>(m_pythonType), attrName));
        if (!value)
            continue;

        // Check if this is a @complete decorator by checking the type name
        const char *typeName = Py_TYPE(value.object())->tp_name;

        // Check for QtBridges.complete decorator type
        if (qstrcmp(typeName, "QtBridges.complete") == 0) {
            // Get the method from the instance (which will bind it)
            Shiboken::AutoDecRef instanceMethod(PyObject_GetAttrString(m_backend, attrName));
            if (!instanceMethod) {
                qCWarning(lcQtBridge, "BridgePyTypeObjectModel: Failed to get instance method: %s", attrName);
                PyErr_Clear();
                continue;
            }

            // Call the method with no arguments
            Shiboken::AutoDecRef emptyTuple(PyTuple_New(0));
            Shiboken::AutoDecRef result(PyObject_Call(instanceMethod.object(), emptyTuple.object(), nullptr));

            if (!result) {
                qCWarning(lcQtBridge, "BridgePyTypeObjectModel: @complete method %s returned NULL", attrName);
                if (PyErr_Occurred()) {
                    std::string error = std::string("BridgePyTypeObjectModel: Error calling @complete decorated method ") + attrName;
                    logPythonException(error.c_str());
                    PyErr_Clear();
                } else {
                    qCWarning(lcQtBridge, "BridgePyTypeObjectModel: No Python error set for failed call");
                }
            }
        }
    }

    // After all @complete methods have executed, emit property change signals for all properties
    // This ensures QML bindings update even when properties are modified from Python code
    if (!m_propertyMap.isEmpty()) {
        for (auto it = m_propertyMap.constBegin(); it != m_propertyMap.constEnd(); ++it) {
            int propertyIndex = it.key();
            emitPropertyChanged(propertyIndex);
        }
    }
}

} // namespace QtBridges
