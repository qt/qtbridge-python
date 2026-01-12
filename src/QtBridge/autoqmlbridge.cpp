// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "autoqmlbridge_p.h"
#include "pycapsule_p.h"
#include "qtbridgelogging_p.h"
#include "errorhandler.h"
#include "conversion_p.h"
#include "updateqmldecorators/updateqmldecorator_p.h"
#include "qmlregistertype_p.h"
#include "helpers_p.h"

#include <sbkpython.h>
#include <autodecref.h>
#include <basewrapper.h>
#include <bindingmanager.h>
#include <gilstate.h>
#include <sbkstring.h>
#include <sbkconverter.h>
#include <signature.h>
#include <pysideproperty_p.h>
#include <pysideclassdecorator_p.h>
#include <signalmanager.h>

#include <QtQml/qqml.h>
#include <QtQml/qqmlprivate.h>
#include <QtCore/qdebug.h>
#include <QtCore/qstring.h>
#include <QtCore/qstringlist.h>
#include <QtCore/qtyperevision.h>

#include <cstring>
#include <mutex>

#if defined(DEBUG_BUILD)
Q_LOGGING_CATEGORY(lcQtBridge, "qtbridges", QtDebugMsg)
#else
Q_LOGGING_CATEGORY(lcQtBridge, "qtbridges", QtWarningMsg)
#endif

/*
This file is a part of the QML bridge implementation and enables the Python backend data model to
be exposed to QML as a QAbstractItemModel.

This file creates a function for the AutoQmlBridge and registers it with the
QtBridges module. The function wraps the Python backend object and exposes it as a
QAbstractItemModel in order to interact with the View models (TablesView, ListView, etc.) in QML.

With respect to a data model in Python, along with wrapping the data model (backend) object
as a QAbstractItemModel, the function also does the following:

1. Registers the methods of the Python backend object as slots in the QMetaObject.
2. All Python properties of the backend object are registered as Qt properties. For each property
    from the backend object, a {property_name}Changed signal is created and registered in the
    QMetaObject. The signal is emitted whenever the property value changes using the corresponding
    setter. Properties that have append functions are registered as ListProperties in QML
3. This file enforces explicit requirements that the user should implement a `data()` and from the
    type of the data returned (list for one dimensional data and pandas Dataframe for tabular data).
    Based on the data returned, the implementation of the various virtual methods of
    QAbstractItemModel should be done.
*/

namespace {

QByteArray getReturnTypeName(PyObject *method, const char *methodName)
{
    // Try to get return type from function annotations
    if (PyObject_HasAttrString(method, "__annotations__")) {
        Shiboken::AutoDecRef annotations(PyObject_GetAttrString(method, "__annotations__"));
        if (annotations && PyDict_Check(annotations.object())) {
            PyObject *returnTypeObj = PyDict_GetItemString(annotations.object(), "return");

            // TODO: Revisit this incase there are performance issues
            // if (returnTypeObj) {
            //     if (PyType_Check(returnTypeObj)) {
            //         const char* name = reinterpret_cast<PyTypeObject*>(returnTypeObj)->tp_name;
            //         if (name) {
            //             if (qstrcmp(name, "str") == 0) return "QString";
            //             if (qstrcmp(name, "int") == 0) return "int";
            //             if (qstrcmp(name, "float") == 0) return "double";
            //             if (qstrcmp(name, "bool") == 0) return "bool";
            //             if (qstrcmp(name, "list") == 0) return "QVariantList";
            //             if (qstrcmp(name, "dict") == 0) return "QVariantMap";
            //             // For other types, use QVariant as fallback
            //             return "QVariant";
            //         }
            //     }
            // }

            if (returnTypeObj && PyType_Check(returnTypeObj)) {
                const char* name = reinterpret_cast<PyTypeObject*>(returnTypeObj)->tp_name;
                if (name) {
                    if (qstrcmp(name, "list") == 0) {
                        qCDebug(lcQtBridge,
                                "Method %s has return type annotation 'list', registering as QVariantList",
                                methodName);
                        return "QVariantList";
                    }
                    if (qstrcmp(name, "dict") == 0) {
                        qCDebug(lcQtBridge,
                                "Method %s has return type annotation 'dict', registering as QVariantMap",
                                methodName);
                        return "QVariantMap";
                    }
                }
                // For all other types, use QVariant as fallback
                qCDebug(lcQtBridge,
                        "Method %s has return type annotation, registering as QVariant",
                        methodName);
                return "QVariant";
            }
        }
    }

    // Default fallback type
    qCWarning(lcQtBridge,
              "Method %s has no return type annotation, defaulting to 'void'",
              methodName);

    return "void";
}

constexpr const char* DATA_METHOD_NAME = "data";

} // anonymous namespace

namespace QtBridges {

// Global map of Python instances to their corresponding QtBridges handler
std::unordered_map<PyObject*, std::shared_ptr<AutoQmlBridgePrivate>> s_bridgeMap;

// Global map for tracking Python objects to BridgePyTypeObjectModel instances
std::unordered_map<PyObject*, BridgePyTypeObjectModel*> s_typeModelMap;

AutoQmlBridgePrivate::AutoQmlBridgePrivate(PyObject *backend, DataType datatype)
    : m_backend(backend), m_pythonType(nullptr), m_mode(BridgeMode::Instance), m_datatype(datatype)
{
    if (m_backend) {
        Py_XINCREF(m_backend);
        m_pythonType = Py_TYPE(m_backend);
        Py_XINCREF(m_pythonType);
    }
    setupMetaObjectBuilder();
}

AutoQmlBridgePrivate::AutoQmlBridgePrivate(PyTypeObject *type)
    : m_backend(nullptr), m_pythonType(type), m_mode(BridgeMode::Type), m_datatype(DataType::Unknown)
{
    if (m_pythonType) {
        Py_XINCREF(m_pythonType);
    }
    setupMetaObjectBuilder();
}

AutoQmlBridgePrivate::AutoQmlBridgePrivate(PyTypeObject *type, const QString &defaultProperty)
    : m_backend(nullptr), m_pythonType(type), m_mode(BridgeMode::Type),
      m_datatype(DataType::Unknown), m_defaultProperty(defaultProperty)
{
    if (m_pythonType) {
        Py_XINCREF(m_pythonType);
    }
    setupMetaObjectBuilder();
}

AutoQmlBridgePrivate::~AutoQmlBridgePrivate()
{
    if (m_backend) {
        Shiboken::GilState gil;
        Py_XDECREF(m_backend);
        m_backend = nullptr;
    }
    if (m_pythonType) {
        Shiboken::GilState gil;
        Py_XDECREF(m_pythonType);
        m_pythonType = nullptr;
    }
    m_model.reset();
    m_metaObjectBuilder.reset();
}

void AutoQmlBridgePrivate::setupMetaObjectBuilder()
{
    if (!m_pythonType) {
        qCDebug(lcQtBridge) << "setupMetaObjectBuilder: m_pythonType is null, returning early";
        return;
    }

    const char* className = m_pythonType->tp_name;
    const QMetaObject *baseMetaObject = &QAbstractItemModel::staticMetaObject;

    m_metaObjectBuilder = std::make_unique<PySide::MetaObjectBuilder>(m_pythonType, baseMetaObject);
    // Add QML.Element class info so QML registration recognizes this as a creatable type
    m_metaObjectBuilder->addInfo("QML.Element", "auto");

    // Add QQmlParserStatus interface info for QML lifecycle hooks
    // This is what Q_INTERFACES(QQmlParserStatus) would add via moc
    m_metaObjectBuilder->addInfo("QML.ParserStatus", "QQmlParserStatus");
    qCDebug(lcQtBridge, "Added QQmlParserStatus interface info for type: %s", className);

    // Add default property if specified
    if (!m_defaultProperty.isEmpty()) {
        m_metaObjectBuilder->addInfo("DefaultProperty", m_defaultProperty.toUtf8().constData());
        qCDebug(lcQtBridge, "Added DefaultProperty class info: %s", qPrintable(m_defaultProperty));
    }

    // Create the model early for instance mode so that registerProperties() can use it
    if (m_mode == BridgeMode::Instance && m_backend) {
        qCDebug(lcQtBridge) << "setupMetaObjectBuilder: Creating model for instance mode (early)";
        m_model = std::make_shared<AutoQmlBridgeModel>(m_backend, baseMetaObject, m_datatype);
        qCDebug(lcQtBridge) << "setupMetaObjectBuilder: Model created successfully (early)";
    }

    // Register methods, properties, and signals
    registerProperties();
    registerMethods();
    // registerSignals();

    // For Type mode, we don't create a model here since BridgePyTypeObjectModel handles that
    qCDebug(lcQtBridge) << "setupMetaObjectBuilder: Completed for class:" << className;
}

void AutoQmlBridgePrivate::registerMethods()
{
    registerMethodsFromType(m_pythonType);
}

void AutoQmlBridgePrivate::registerProperties()
{
    registerPropertiesFromType(m_pythonType);
}

void AutoQmlBridgePrivate::registerSignals()
{
    registerSignalsFromType(m_pythonType);
}

void AutoQmlBridgePrivate::registerMethodsFromType(PyTypeObject *type)
{
    if (!type) return;

    // For instance mode, use the backend instance; for type mode, use the type directly
    PyObject *sourceObject = (m_mode == BridgeMode::Instance) ? m_backend : reinterpret_cast<PyObject*>(type);

    // Use PyObject_Dir to get all attributes including inherited ones, not just direct class dict
    Shiboken::AutoDecRef dirList(PyObject_Dir(reinterpret_cast<PyObject*>(type)));
    if (!dirList)
        return;

    const Py_ssize_t count = PyList_Size(dirList.object());
    for (Py_ssize_t i = 0; i < count; ++i) {
        PyObject *nameObj = PyList_GetItem(dirList.object(), i);
        if (!PyUnicode_Check(nameObj))
            continue;

        const char *methodName = Shiboken::String::toCString(nameObj);
        Shiboken::AutoDecRef value(PyObject_GetAttrString(reinterpret_cast<PyObject*>(type), methodName));
        if (!value)
            continue;

        if (PyCallable_Check(value.object())) {
                // Ignore methods that start with "_"
                if (methodName[0] == '_')
                    continue;

                // For type mode, we don't require the data() method
                if (m_mode == BridgeMode::Type && qstrcmp(methodName, "data") == 0)
                    continue;

                // For instance mode, ignore the data method as it's handled separately
                if (m_mode == BridgeMode::Instance && qstrcmp(methodName, "data") == 0)
                    continue;

                // Ignore methods that have the @property decorator
                if (PyObject_TypeCheck(value, &PyProperty_Type))
                    continue;

                // Get return type from method annotations
                QByteArray returnType = getReturnTypeName(value, methodName);

                QByteArray signature = QByteArray(methodName) + '(';

                // Set all parameters to QVariant
                PyObject *funcObj = value.object();
                Shiboken::AutoDecRef codeObj;

                // Check if this is an updateQML decorator
                // it does not have the __code__ object
                if (qstrcmp(Py_TYPE(funcObj)->tp_name, "QtBridges.insert") == 0 ||
                    qstrcmp(Py_TYPE(funcObj)->tp_name, "QtBridges.remove") == 0 ||
                    qstrcmp(Py_TYPE(funcObj)->tp_name, "QtBridges.move") == 0 ||
                    qstrcmp(Py_TYPE(funcObj)->tp_name, "QtBridges.edit") == 0 ||
                    qstrcmp(Py_TYPE(funcObj)->tp_name, "QtBridges.reset") == 0 ||
                    qstrcmp(Py_TYPE(funcObj)->tp_name, "QtBridges.complete") == 0) {
                    auto *pData = PySide::ClassDecorator::DecoratorPrivate::get<QtBridges::UpdateQMLDecoratorPrivate>(funcObj);

                    // For bridge_instance(), we can safely set the backend instance since
                    // there's only one instance. For bridge_type(), m_backend is nullptr here
                    // and decorators will get the backend dynamically when called.
                    if (pData && m_backend) {
                        pData->setBackendInstance(m_backend);
                    }

                    funcObj = pData ? pData->getWrappedFunc() : nullptr;

                    if (funcObj) {
                        codeObj.reset(PyObject_GetAttrString(funcObj, "__code__"));
                    } else {
                        QByteArray errorMsg = QByteArray("Cannot introspect Python method '")
                            + methodName
                            + "' (missing wrapped_func attribute in insert/remove/move/edit/reset decorator)";
                        PyErr_SetString(PyExc_RuntimeError, errorMsg.constData());
                        return;
                    }

                } else {
                    // while loop for nested decorators
                    while (funcObj && !PyObject_HasAttrString(funcObj, "__code__") &&
                        PyObject_HasAttrString(funcObj, "__wrapped__")) {
                        Shiboken::AutoDecRef wrapped(PyObject_GetAttrString(funcObj, "__wrapped__"));
                        Py_XDECREF(funcObj);
                        funcObj = wrapped.object();
                    }
                    if (funcObj && PyObject_HasAttrString(funcObj, "__code__")) {
                        codeObj.reset(PyObject_GetAttrString(funcObj, "__code__"));
                    }
                }

                if (codeObj) {
                    Shiboken::AutoDecRef argcount(PyObject_GetAttrString(codeObj.object(), "co_argcount"));
                    if (argcount) {
                        int count = PyLong_AsLong(argcount.object());
                        for (int i = 1; i < count; ++i) {
                            if (i > 1) {
                                signature += ", ";
                            }
                            signature += "QVariant";
                        }
                    }
                    signature += ')';
                } else {
                    // Raise error if code object does not exist
                    QByteArray errorMsg = QByteArray("Cannot introspect Python method '")
                        + methodName
                        + "' (missing __code__ attribute)";
                    PyErr_SetString(PyExc_RuntimeError, errorMsg.constData());
                    return;
                }

                // Register the slot with return type
                m_metaObjectBuilder->addSlot(signature, returnType);
                qCDebug(lcQtBridge) << "Registered method:" << signature;
        }
    }
}

void AutoQmlBridgePrivate::registerPropertiesFromType(PyTypeObject *type)
{
    if (!type) return;

    // For type mode, inspect the type directly
    Shiboken::AutoDecRef dirList(PyObject_Dir(reinterpret_cast<PyObject*>(type)));
    if (!dirList)
        return;

    const Py_ssize_t count = PyList_Size(dirList.object());
    for (Py_ssize_t i = 0; i < count; ++i) {
        PyObject *nameObj = PyList_GetItem(dirList.object(), i);
        if (!PyUnicode_Check(nameObj))
            continue;

        QByteArray attrName = Shiboken::String::toCString(nameObj);
        Shiboken::AutoDecRef classDescriptor(
            PyObject_GetAttrString(reinterpret_cast<PyObject*>(type), attrName.constData()));
        if (!classDescriptor)
            continue;

        // check if classDescriptor is from a Python property
        if (!PyObject_TypeCheck(classDescriptor.object(), &PyProperty_Type))
            continue;

        // Use helper function to register the property (instance mode - with meta-object builder)
        PySideProperty *property = registerSingleProperty(
            attrName, classDescriptor.object(), nullptr, m_metaObjectBuilder.get(), m_model.get());

        if (property)
            qCDebug(lcQtBridge, "Registered property %s for type %s with notify signal",
                    attrName.constData(), type->tp_name);
    }
}

void AutoQmlBridgePrivate::registerSignalsFromType(PyTypeObject *type)
{
    // Use MetaObjectBuilder to register signals
    // This can be extended later for custom signal registration from type introspection
    Q_UNUSED(type);
}

AutoQmlBridgeModel* AutoQmlBridgePrivate::model() const
{
    return m_model.get();
}

PyObject *AutoQmlBridgePrivate::bridge_instance(PyObject *self, PyObject *args, PyObject *kwds)
{
    Q_UNUSED(self);
    PyObject *instance = nullptr;
    const char *name_str = nullptr;
    const char *uri_str = "backend";  // Default URI

    static const char *kwlist[] = {"instance", "name", "uri", nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Os|s", const_cast<char **>(kwlist),
                                     &instance, &name_str, &uri_str)) {
        return nullptr;
    }

    if (!instance) {
        PyErr_SetString(PyExc_ValueError, "bridge_instance requires a valid Python instance");
        QtBridges::logPythonException("bridge_instance");
        return nullptr;
    }

    // Check if the user data model has a data() method
    if (!PyObject_HasAttrString(instance, DATA_METHOD_NAME)) {
        PyErr_SetString(PyExc_TypeError,
                        "The class wrapped with bridge_instance must have a data() method that "
                        "returns the data to be passed to QML");
        QtBridges::logPythonException("bridge_instance");
        return nullptr;
    }

    // Try to infer data type from the instance
    QtBridges::DataType dataType = inferDataType(instance);
    if (dataType == QtBridges::DataType::Unknown) {
        PyErr_SetString(PyExc_TypeError,
                      "Could not infer data type from data() method. "
                      "Please add a return type hint to your data() method, e.g.:\n"
                      "  def data(self) -> list[str]: ...  # For simple lists\n"
                      "  def data(self) -> List[MyDataClass]: ...  # For dataclass lists\n\n"
                      "Supported return types:\n"
                      "  - list[str], list[int], list[float] (primitive lists)\n"
                      "  - List[DataClass], list[DataClass] (dataclass lists)");
        QtBridges::logPythonException("bridge_instance");
        return nullptr;
    }

    // Log the actual inferred type name
    const char* inferredTypeName = "Unknown";
    switch (dataType) {
        case QtBridges::DataType::List: inferredTypeName = "List"; break;
        case QtBridges::DataType::DataClassList: inferredTypeName = "DataClassList"; break;
        case QtBridges::DataType::Table: inferredTypeName = "Table"; break;
        default: break;
    }
    qCDebug(lcQtBridge, "Inferred data_type: %s", inferredTypeName);

    try {
        // Use the provided name for QML registration
        const char *qmlName = name_str;
        qCDebug(lcQtBridge, "Registering instance with QML name: %s", qmlName);

        // Create bridge instance directly using constructor (which already sets up meta object)
        auto data = std::make_shared<AutoQmlBridgePrivate>(instance, dataType);

        // Finalize the meta object after construction
        data->finalizeMetaObject();

        // Verify if methods added - to be removed later
        // int methodCount = data->model()->metaObject()->methodCount();
        // for (int i = 0; i < methodCount; ++i) {
        //     QMetaMethod method = data->model()->metaObject()->method(i);
        //     qCDebug(lcQtBridge) << "Method:" << method.methodSignature()
        //                       << ", Return type:" << method.typeName();
        // }

        // verify if properties added - to be removed later
        // int propertyCount = data->m_model->metaObject()->propertyCount();
        // for (int i = 0; i < propertyCount; ++i) {
        //     QMetaProperty property = data->m_model->metaObject()->property(i);
        //     qCDebug(lcQtBridge) << "Property:" << property.name()
        //             << ", Type:" << property.typeName();
        // }

        // Print all signals in the metaObject
        // const QMetaObject *mo = data->model()->metaObject();
        // int methodCount = mo->methodCount();
        // for (int i = 0; i < methodCount; ++i) {
        //     QMetaMethod method = mo->method(i);
        //     if (method.methodType() == QMetaMethod::Signal) {
        //         qCDebug(lcQtBridge) << "Signal:" << method.methodSignature();
        //     }
        // }

        // Register the model with the QML engine as singleton
        qmlRegisterSingletonInstance(
            uri_str, 1, 0, qmlName, data->model());

        // Store the bridge instance
        s_bridgeMap[instance] = data;

        Py_RETURN_NONE;
    } catch (const std::exception& e) {
        PyErr_Format(PyExc_RuntimeError, "Failed to create bridge_instance: %s", e.what());
        QtBridges::logPythonException("bridge_instance");
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "Unknown error creating bridge_instance");
        QtBridges::logPythonException("bridge_instance");
        return nullptr;
    }
}

PyObject *AutoQmlBridgePrivate::bridge_type(PyObject *self, PyObject *args, PyObject *kwds)
{
    Q_UNUSED(self);
    PyTypeObject *type = nullptr;
    const char *uri = "backend";
    const char *version = "1.0";
    const char *qmlName = nullptr;
    const char *defaultProperty = nullptr;

    static const char *kwlist[] = {"type", "uri", "version", "name", "default_property", nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, kwds,
                                     "O!|ssss",
                                     const_cast<char **>(kwlist),
                                     &PyType_Type,
                                     &type,
                                     &uri,
                                     &version,
                                     &qmlName,
                                     &defaultProperty)) {
        return nullptr;
    }

    if (!type) {
        PyErr_SetString(PyExc_ValueError, "bridge_type requires a valid Python type");
        return nullptr;
    }

    // Parse version string
    QVersionNumber versionNumber = QVersionNumber::fromString(QString::fromUtf8(version));
    if (versionNumber.isNull() || versionNumber.segmentCount() < 2) {
        PyErr_SetString(PyExc_ValueError, "version must be in format 'major.minor'");
        return nullptr;
    }

    int versionMajor = versionNumber.majorVersion();
    int versionMinor = versionNumber.minorVersion();

    // Use type name if qmlName not provided
    const char *qml_name = qmlName ? qmlName : type->tp_name;

    try {
        // Check if this type is already registered
        if (getAutoQmlBridgePrivateForType(type) != nullptr) {
            qCWarning(lcQtBridge) << "Python type" << qml_name << "is already registered";
            Py_RETURN_NONE;
        }

        qCDebug(lcQtBridge, "Registering Python type %s as QML type %s in module %s %d.%d",
                type->tp_name, qml_name, uri, versionMajor, versionMinor);

        // Create bridge handler for this type to generate the dynamic metaObject
        AutoQmlBridgePrivate *bridge;
        if (defaultProperty && strlen(defaultProperty) > 0) {
            bridge = new AutoQmlBridgePrivate(type, QString::fromUtf8(defaultProperty));
            qCDebug(lcQtBridge, "Using default property: %s", defaultProperty);
        } else {
            bridge = new AutoQmlBridgePrivate(type);
        }
        const QMetaObject *dynamicMetaObject = bridge->finalizeMetaObject();
        if (!dynamicMetaObject) {
            delete bridge;
            PyErr_SetString(PyExc_RuntimeError, "Failed to create dynamic metaObject for Python type");
            return nullptr;
        }

        // Store the bridge instance permanently via PyCapsule
        storeAutoQmlBridgePrivateForType(type, bridge);

        // Store the Python type -> dynamic meta object mapping permanently
        storeDynamicMetaObjectForType(type, dynamicMetaObject);

        // Register the QML type using the dedicated function
        int result = registerQmlType(type, dynamicMetaObject, uri, versionMajor, versionMinor, qml_name);
        if (result == -1) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to register type with QML engine");
            return nullptr;
        }

        qCDebug(lcQtBridge, "Successfully registered Python type %s as QML type %s (result: %d)",
                type->tp_name, qml_name, result);

        Py_RETURN_NONE;

    } catch (const std::exception& e) {
        std::string error = "Exception in bridge_type: " + std::string(e.what());
        PyErr_SetString(PyExc_RuntimeError, error.c_str());
        logPythonException(error.c_str());
        return nullptr;
    } catch (...) {
        const char* error = "Unknown exception in bridge_type";
        PyErr_SetString(PyExc_RuntimeError, error);
        logPythonException(error);
        return nullptr;
    }
}

const QMetaObject *AutoQmlBridgePrivate::finalizeMetaObject()
{

    if (!m_metaObjectBuilder) {
        qCWarning(lcQtBridge) << "finalizeMetaObject: m_metaObjectBuilder is null";
        return nullptr;
    }

    qCDebug(lcQtBridge) << "finalizeMetaObject: Calling metaObjectBuilder->update()";
    const QMetaObject *newMetaObject = m_metaObjectBuilder->update();

    if (m_model) {
        qCDebug(lcQtBridge) << "finalizeMetaObject: Setting dynamic meta object on model";
        m_model->setDynamicMetaObject(newMetaObject);
    }

    qCDebug(lcQtBridge) << "finalizeMetaObject: Finalization completed";
    return newMetaObject;
}

void AutoQmlBridgePrivate::setBackend(PyObject *backend)
{
    if (m_backend) {
        Py_XDECREF(m_backend);
    }
    m_backend = backend;
    Py_XINCREF(m_backend);
}

} // namespace QtBridges

void initAutoQmlBridge(PyObject *module)
{
    // Initialize conversion functions
    QtBridges::registerPyObjectMetaTypeConversions();

    static PyMethodDef bridge_instanceDef = {
        "bridge_instance",
        (PyCFunction)QtBridges::AutoQmlBridgePrivate::bridge_instance,
        METH_VARARGS | METH_KEYWORDS,
        "bridge_instance(instance: object, name: str) -> None\n\n"
        "Adapts a Python object as a QAbstractItemModel for QML.\n\n"
        "Args:\n"
        "    instance: A Python object with a data() method that returns the model data\n"
        "    name: The name to use when registering with QML\n\n"
        "Note:\n"
        "    Use type hints on the data() method to help infer the data type."
    };

    static PyMethodDef bridge_typeDef = {
        "bridge_type",
        (PyCFunction)QtBridges::AutoQmlBridgePrivate::bridge_type,
        METH_VARARGS | METH_KEYWORDS,
        "bridge_type(type: type, uri: str = 'backend', version: str = '1.0', name: str = None, "
        "default_property: str = None) -> None\n\n"
        "Prepares a Python type for QML registration and analyzes its structure.\n\n"
        "Args:\n"
        "    type: A Python type to analyze and prepare for QML integration\n"
        "    uri: QML module URI (default: 'backend')\n"
        "    version: QML module version (default: '1.0')\n"
        "    name: Name to use in QML (default: type name)\n"
        "    default_property: Property name for QML default property (optional)\n\n"
        "The type must have a data() method for QML model compatibility."
    };

    PyObject *bridge_instanceFunc = PyCFunction_New(&bridge_instanceDef, nullptr);
    PyObject *bridge_typeFunc = PyCFunction_New(&bridge_typeDef, nullptr);

    if (!bridge_instanceFunc || !bridge_typeFunc) {
        return;
    }

    PyModule_AddObject(module, "bridge_instance", bridge_instanceFunc);
    PyModule_AddObject(module, "bridge_type", bridge_typeFunc);
}