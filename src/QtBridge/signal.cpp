// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "signal_p.h"
#include "qtbridgelogging_p.h"
#include "errorhandler.h"
#include "autoqmlbridge_p.h"
#include "autoqmlbridgemodel_p.h"

#include <shiboken.h>
#include <qobjectconnect.h>
#include <signalmanager.h>
#include <pep384ext.h>

#include <QtCore/qbytearray.h>
#include <cstring>

// Forward declarations
namespace QtBridges::Signal {
    QByteArray pythonTypeToQtTypeName(PyObject *type);
    bool isSignal(PyObject *obj);
    QObject *getSignalSource(QtBridgeSignalInstance *signalInstance);
    PyObject *createSignalInstance(QtBridgeSignal *signal, PyObject *source);
}

extern "C"
{

static void Signal_dealloc(QtBridgeSignal *self)
{
    Py_XDECREF(self->signalName);
    Py_XDECREF(self->signatureArgs);
    PyObject_Free(self);
}

static int Signal_init(QtBridgeSignal *self, PyObject *args, PyObject *kwds)
{
    // Signal() is called with positional arguments representing the signal parameter types
    // e.g., Signal(str, int) -> args is (str, int)

    Q_UNUSED(kwds);

    // Convert Python type arguments to Qt type names
    PyObject *qtTypeNames = PyTuple_New(PyTuple_Size(args));
    if (!qtTypeNames) {
        return -1;
    }

    for (Py_ssize_t i = 0; i < PyTuple_Size(args); ++i) {
        PyObject *pyType = PyTuple_GetItem(args, i);
        QByteArray qtTypeName = QtBridges::Signal::pythonTypeToQtTypeName(pyType);

        PyObject *qtTypeStr = Shiboken::String::fromCString(qtTypeName.constData());
        if (!qtTypeStr) {
            Py_DECREF(qtTypeNames);
            return -1;
        }

        PyTuple_SetItem(qtTypeNames, i, qtTypeStr); // Steals reference
    }

    // Store the converted Qt type names
    self->signatureArgs = qtTypeNames;

    // Signal name will be set later
    self->signalName = nullptr;

    qCDebug(lcQtBridge) << "Signal.__init__ called with" << PyTuple_Size(args) << "type arguments";

    return 0;
}

// Signal __get__ descriptor method
// This is called when the signal is accessed as a class or instance attribute
static PyObject* Signal_get(QtBridgeSignal *self, PyObject *obj, PyObject *type)
{
    Q_UNUSED(type);

    // If accessed from the class (not an instance), return the signal descriptor itself
    if (obj == nullptr || obj == Py_None) {
        Py_INCREF(self);
        return reinterpret_cast<PyObject*>(self);
    }

    return QtBridges::Signal::createSignalInstance(self, obj);
}

// Signal __set_name__ method (called when the signal is assigned to a class attribute)
static PyObject* Signal_set_name(QtBridgeSignal *self, PyObject *args)
{
    PyObject *owner, *name;
    if (!PyArg_ParseTuple(args, "OO", &owner, &name)) {
        return nullptr;
    }

    if (!PyUnicode_Check(name)) {
        PyErr_SetString(PyExc_TypeError, "__set_name__ expects a string name");
        return nullptr;
    }

    // Store the signal name
    Py_XDECREF(self->signalName);
    Py_INCREF(name);
    self->signalName = name;

    Py_RETURN_NONE;
}

// Signal __repr__ method
static PyObject* Signal_repr(QtBridgeSignal *self)
{
    const char *name = self->signalName ? Shiboken::String::toCString(self->signalName) : "<unnamed>";
    return PyUnicode_FromFormat("<QtBridge.Signal '%s'>", name);
}

static PyMethodDef Signal_methods[] = {
    {"__set_name__", reinterpret_cast<PyCFunction>(Signal_set_name), METH_VARARGS,
     "Called when signal is assigned to a class attribute"},
    {nullptr, nullptr, 0, nullptr}
};

// Create the Signal type
static PyTypeObject *createSignalType()
{
    PyType_Slot SignalType_slots[] = {
        {Py_tp_dealloc, reinterpret_cast<void *>(Signal_dealloc)},
        {Py_tp_repr, reinterpret_cast<void *>(Signal_repr)},
        {Py_tp_descr_get, reinterpret_cast<void *>(Signal_get)},
        {Py_tp_methods, reinterpret_cast<void *>(Signal_methods)},
        {Py_tp_init, reinterpret_cast<void *>(Signal_init)},
        {Py_tp_new, reinterpret_cast<void *>(PyType_GenericNew)},
        {0, nullptr}
    };

    PyType_Spec SignalType_spec = {
        "QtBridge.Signal",
        sizeof(QtBridgeSignal),
        0,
        Py_TPFLAGS_DEFAULT,
        SignalType_slots,
    };

    return reinterpret_cast<PyTypeObject *>(PyType_FromSpec(&SignalType_spec));
}

PyTypeObject *QtBridgeSignal_TypeF()
{
    static auto *type = createSignalType();
    return type;
}

// ============================================================================
// SignalInstance implementation
// ============================================================================

static void SignalInstance_dealloc(QtBridgeSignalInstance *self)
{
    delete self->signature;
    // Note: source is a borrowed ref, don't decref
    PyObject_Free(self);
}

static PyObject *SignalInstance_repr(QtBridgeSignalInstance *self)
{
    const char *sig = self->signature ? self->signature->constData() : "<unnamed>";
    return PyUnicode_FromFormat("<QtBridge.SignalInstance '%s' at %p>", sig, self);
}

static PyObject *SignalInstance_connect(PyObject *self, PyObject *args, PyObject *kwds)
{
    static const char *kwlist[] = {"slot", "type", nullptr};
    PyObject *slot = nullptr;
    int connectionType = static_cast<int>(Qt::AutoConnection);

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i", const_cast<char **>(kwlist),
                                     &slot, &connectionType)) {
        return nullptr;
    }

    if (!PyCallable_Check(slot)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a callable (slot)");
        return nullptr;
    }

    auto *signalInstance = reinterpret_cast<QtBridgeSignalInstance *>(self);

    // Get the QObject source
    QObject *source = QtBridges::Signal::getSignalSource(signalInstance);
    if (!source)
        return nullptr;

    // Use pre-computed signature with SIGNAL() prefix
    QByteArray qSignalSignature = QByteArray("2") + *signalInstance->signature;  // '2' is SIGNAL prefix

    qCDebug(lcQtBridge) << "SignalInstance.connect: signal=" << *signalInstance->signature
                        << "source=" << source;

    // Use PySide's qobjectConnectCallback to connect the Python callable
    auto conn = PySide::qobjectConnectCallback(source, qSignalSignature.constData(),
                                               slot, static_cast<Qt::ConnectionType>(connectionType));

    if (!conn) {
        qCWarning(lcQtBridge) << "SignalInstance.connect failed for signal:" << *signalInstance->signature;
        PyErr_SetString(PyExc_RuntimeError, "Failed to connect signal");
        return nullptr;
    }

    qCDebug(lcQtBridge) << "SignalInstance.connect succeeded";
    Py_RETURN_TRUE;
}

static PyObject *SignalInstance_disconnect(PyObject *self, PyObject *args)
{
    PyObject *slot = Py_None;
    if (!PyArg_ParseTuple(args, "|O", &slot)) {
        return nullptr;
    }

    auto *signalInstance = reinterpret_cast<QtBridgeSignalInstance *>(self);

    // Get the QObject source
    QObject *source = QtBridges::Signal::getSignalSource(signalInstance);
    if (!source)
        return nullptr;

    // Use pre-computed signature with SIGNAL() prefix
    QByteArray qSignalSignature = QByteArray("2") + *signalInstance->signature;

    qCDebug(lcQtBridge) << "SignalInstance.disconnect: signal=" << *signalInstance->signature
                        << "source=" << source;

    bool ok = false;
    if (slot == Py_None) {
        // Disconnect all slots from this signal
        ok = source->disconnect(qSignalSignature.constData());
    } else if (PyCallable_Check(slot)) {
        // Disconnect a specific Python callable
        ok = PySide::qobjectDisconnectCallback(source, qSignalSignature.constData(), slot);
    } else {
        PyErr_SetString(PyExc_TypeError, "Argument must be a callable or None");
        return nullptr;
    }

    if (ok) {
        qCDebug(lcQtBridge) << "SignalInstance.disconnect succeeded";
        Py_RETURN_TRUE;
    }

    qCDebug(lcQtBridge) << "SignalInstance.disconnect: no connection found";
    Py_RETURN_FALSE;
}

static PyObject *SignalInstance_emit(PyObject *self, PyObject *args)
{
    auto *signalInstance = reinterpret_cast<QtBridgeSignalInstance *>(self);

    // Get the QObject source
    QObject *source = QtBridges::Signal::getSignalSource(signalInstance);
    if (!source)
        return nullptr;

    // Use pre-computed signature with SIGNAL() prefix
    QByteArray qSignalSignature = QByteArray("2") + *signalInstance->signature;

    qCDebug(lcQtBridge) << "SignalInstance.emit: signal=" << *signalInstance->signature
                        << "source=" << source
                        << "args count=" << PyTuple_Size(args);

    // Use PySide's SignalManager to emit the signal
    const bool ok = PySide::SignalManager::emitSignal(source, qSignalSignature.constData(), args);

    if (PyErr_Occurred()) {
        return nullptr;
    }

    if (ok) {
        qCDebug(lcQtBridge) << "SignalInstance.emit succeeded";
        Py_RETURN_TRUE;
    }

    qCWarning(lcQtBridge) << "SignalInstance.emit failed for signal:" << *signalInstance->signature;
    Py_RETURN_FALSE;
}

// SignalInstance __call__ method
// handles signal() invocation
static PyObject *SignalInstance_call(PyObject *self, PyObject *args, PyObject *kwds)
{
    auto *signalInstance = reinterpret_cast<QtBridgeSignalInstance *>(self);
    return SignalInstance_emit(self, args);
}

static PyMethodDef SignalInstance_methods[] = {
    {"connect", reinterpret_cast<PyCFunction>(SignalInstance_connect),
                METH_VARARGS | METH_KEYWORDS, "Connect a slot to this signal"},
    {"disconnect", SignalInstance_disconnect, METH_VARARGS,
                   "Disconnect a slot from this signal"},
    {"emit", SignalInstance_emit, METH_VARARGS, "Emit this signal with arguments"},
    {nullptr, nullptr, 0, nullptr}
};

static PyTypeObject *createSignalInstanceType()
{
    PyType_Slot SignalInstanceType_slots[] = {
        {Py_tp_call, reinterpret_cast<void *>(SignalInstance_call)},
        {Py_tp_dealloc, reinterpret_cast<void *>(SignalInstance_dealloc)},
        {Py_tp_repr, reinterpret_cast<void *>(SignalInstance_repr)},
        {Py_tp_methods, reinterpret_cast<void *>(SignalInstance_methods)},
        {Py_tp_new, reinterpret_cast<void *>(PyType_GenericNew)},
        {0, nullptr}
    };

    PyType_Spec SignalInstanceType_spec = {
        "QtBridge.SignalInstance",
        sizeof(QtBridgeSignalInstance),
        0,
        Py_TPFLAGS_DEFAULT,
        SignalInstanceType_slots,
    };

    return reinterpret_cast<PyTypeObject *>(PyType_FromSpec(&SignalInstanceType_spec));
}

PyTypeObject *QtBridgeSignalInstance_TypeF()
{
    static auto *type = createSignalInstanceType();
    return type;
}

} // extern "C"

// Helper functions in QtBridges::Signal namespace
namespace QtBridges {
namespace Signal {

// Convert Python type to Qt type name for signal signatures
QByteArray pythonTypeToQtTypeName(PyObject *pyType)
{
    if (!pyType)
        return "QVariant";

    // Handle None/void
    if (pyType == Py_None)
        return "void";

    // Check built-in types
    if (PyType_Check(pyType)) {
        const char *typeName = Shiboken::String::toCString(PyObject_Str(pyType));
        if (!typeName)
            return "QVariant";

        // Check for common Python types (str, int, float, bool, list, dict)
        if (std::strstr(typeName, "str") != nullptr)
            return "QString";
        if (std::strstr(typeName, "int") != nullptr)
            return "int";
        if (std::strstr(typeName, "float") != nullptr)
            return "double";
        if (std::strstr(typeName, "bool") != nullptr)
            return "bool";
        if (std::strstr(typeName, "list") != nullptr)
            return "QVariantList";
        if (std::strstr(typeName, "dict") != nullptr)
            return "QVariantMap";
    }

    // Handle string type names directly
    // eg: Signal("int")
    if (PyUnicode_Check(pyType)) {
        const char *typeName = Shiboken::String::toCString(pyType);
        if (std::strcmp(typeName, "str") == 0)
            return "QString";
        if (std::strcmp(typeName, "int") == 0)
            return "int";
        if (std::strcmp(typeName, "float") == 0)
            return "double";
        if (std::strcmp(typeName, "bool") == 0)
            return "bool";
        // Return as-is for custom types
        return QByteArray(typeName);
    }

    // Default to QVariant for unknown types
    return "QVariant";
}

int init(PyObject *module)
{
    auto *signalType = QtBridgeSignal_TypeF();
    if (!signalType) {
        qCWarning(lcQtBridge) << "Failed to create QtBridge.Signal type";
        return -1;
    }

    Py_INCREF(signalType);
    if (PyModule_AddObject(module, "Signal", reinterpret_cast<PyObject*>(signalType)) < 0) {
        Py_DECREF(signalType);
        qCWarning(lcQtBridge) << "Failed to add QtBridge.Signal to module";
        return -1;
    }

    // Also register the SignalInstance type
    auto *signalInstanceType = QtBridgeSignalInstance_TypeF();
    if (!signalInstanceType) {
        qCWarning(lcQtBridge) << "Failed to create QtBridge.SignalInstance type";
        return -1;
    }

    Py_INCREF(signalInstanceType);
    if (PyModule_AddObject(module, "SignalInstance", reinterpret_cast<PyObject*>(signalInstanceType)) < 0) {
        Py_DECREF(signalInstanceType);
        qCWarning(lcQtBridge) << "Failed to add QtBridge.SignalInstance to module";
        return -1;
    }

    qCDebug(lcQtBridge) << "QtBridge.Signal and SignalInstance types initialized successfully";
    return 0;
}

bool isSignal(PyObject *obj)
{
    return obj && PyObject_TypeCheck(obj, QtBridgeSignal_TypeF());
}

const char* getName(PyObject *signalObj)
{
    if (!isSignal(signalObj))
        return nullptr;

    QtBridgeSignal *signal = reinterpret_cast<QtBridgeSignal*>(signalObj);
    if (signal->signalName && PyUnicode_Check(signal->signalName)) {
        return Shiboken::String::toCString(signal->signalName);
    }
    return nullptr;
}

PyObject* getArgs(PyObject *signalObj)
{
    if (!isSignal(signalObj))
        return nullptr;

    QtBridgeSignal *signal = reinterpret_cast<QtBridgeSignal*>(signalObj);
    return signal->signatureArgs;
}

QByteArray buildSignature(PyObject *signalObj)
{
    if (!isSignal(signalObj))
        return {};

    QtBridgeSignal *signal = reinterpret_cast<QtBridgeSignal*>(signalObj);

    // Get the signal name
    const char *name = signal->signalName ? Shiboken::String::toCString(signal->signalName) : nullptr;
    if (!name)
        return {};

    // Build signature: "signalName(type1,type2,...)"
    QByteArray signature(name);
    signature.append('(');

    if (signal->signatureArgs && PyTuple_Check(signal->signatureArgs)) {
        Py_ssize_t argc = PyTuple_Size(signal->signatureArgs);
        for (Py_ssize_t i = 0; i < argc; ++i) {
            if (i > 0)
                signature.append(',');
            PyObject *typeStr = PyTuple_GetItem(signal->signatureArgs, i);
            if (typeStr && PyUnicode_Check(typeStr)) {
                signature.append(Shiboken::String::toCString(typeStr));
            }
        }
    }

    signature.append(')');
    return signature;
}

QObject *getSignalSource(QtBridgeSignalInstance *signalInstance)
{
    if (!signalInstance->source) {
        PyErr_SetString(PyExc_RuntimeError, "SignalInstance has no source object");
        return nullptr;
    }

    // Look up the AutoQmlBridgePrivate from the global map
    auto it = s_bridgeMap.find(signalInstance->source);
    if (it == s_bridgeMap.end()) {
        // Try the typeModelMap for type-based bridges
        auto typeIt = s_typeModelMap.find(signalInstance->source);
        if (typeIt != s_typeModelMap.end()) {
            return typeIt->second;  // BridgePyTypeObjectModel is a QObject
        }
        PyErr_SetString(PyExc_RuntimeError,
            "Source object is not registered with QtBridge. "
            "Ensure the object is wrapped with bridge_instance() or instantiated via bridge_type().");
        return nullptr;
    }

    AutoQmlBridgeModel *model = it->second->model();
    if (!model) {
        PyErr_SetString(PyExc_RuntimeError, "AutoQmlBridgeModel is not available");
        return nullptr;
    }

    return model;
}

// Helper function to create a SignalInstance from a Signal and source object
PyObject *createSignalInstance(QtBridgeSignal *signal, PyObject *source)
{
    PyTypeObject *type = QtBridgeSignalInstance_TypeF();
    if (!type) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get SignalInstance type");
        return nullptr;
    }

    auto *instance = PyObject_New(QtBridgeSignalInstance, type);
    if (!instance) {
        return nullptr;
    }

    // Store borrowed reference to source
    // the source will outlive the instance
    instance->source = source;


    // Pre-compute the signature using buildSignature from the Signal descriptor
    instance->signature = new QByteArray(buildSignature(
        reinterpret_cast<PyObject *>(signal)));

    return reinterpret_cast<PyObject *>(instance);
}

// Check if a method has overwritten a Signal in the class hierarchy.
// If so, raise a clear error
//
// IMPORTANT: This function can only detect inherited signal conflicts, where a
// derived class defines a method that shadows a signal from a base class.
//
// Same-class conflicts (signal and method defined in the same class) cannot be
// detected because Python's descriptor protocol doesn't call __set_name__ when
// the descriptor is immediately overwritten in the same class body. Python
// processes the class body sequentially, so by the time the method definition
// executes, it simply replaces the signal in the class dict, and __set_name__
// is never invoked for the now-unreachable signal descriptor.
//
// Example that CAN be detected (inherited conflict):
//   class Base:
//       mySignal = Signal(int)  # __set_name__ IS called
//   class Derived(Base):
//       def mySignal(self): pass  # detectHomonymousMethodError will catch this
//
// Example that cannot be detected (same-class conflict):
//   class MyClass:
//       mySignal = Signal(int)    # Assigned to dict
//       def mySignal(self): pass  # Overwrites before __set_name__ runs
void detectHomonymousMethodError(PyTypeObject *cls)
{
    if (!cls)
        return;

    // Get the MRO to check base classes
    Shiboken::AutoDecRef mroObj(PyObject_GetAttrString(reinterpret_cast<PyObject*>(cls), "__mro__"));
    if (!mroObj || !PyTuple_Check(mroObj))
        return;

    PyObject *mro = mroObj.object();
    Py_ssize_t mroSize = PyTuple_Size(mro);

    // Iterate through the current class's attributes
    PyObject *clsDict = PepType_GetDict(cls);
    if (!clsDict)
        return;

    PyObject *key, *value;
    Py_ssize_t pos = 0;

    while (PyDict_Next(clsDict, &pos, &key, &value)) {
        if (!PyCallable_Check(value))
            continue;

        // For each callable in the current class, check if any base class has a Signal with the same name
        for (Py_ssize_t i = 1; i < mroSize; ++i) {  // Start from 1 to skip the class itself
            PyObject *base = PyTuple_GetItem(mro, i);
            if (!PyType_Check(base))
                continue;

            PyTypeObject *baseType = reinterpret_cast<PyTypeObject*>(base);
            PyObject *baseDict = PepType_GetDict(baseType);
            if (!baseDict)
                continue;

            // Check if base class has an attribute with this name
            PyObject *baseAttr = PyDict_GetItem(baseDict, key);
            if (baseAttr && isSignal(baseAttr)) {
                // Found a Signal in a base class that's been overwritten by a method!
                const char *signalName = Shiboken::String::toCString(key);

                Shiboken::AutoDecRef clsNameObj(PyObject_GetAttrString(reinterpret_cast<PyObject*>(cls), "__name__"));
                Shiboken::AutoDecRef baseNameObj(PyObject_GetAttrString(base, "__name__"));

                const char *className = clsNameObj.isNull() ? "<unknown>" : Shiboken::String::toCString(clsNameObj);
                const char *baseName = baseNameObj.isNull() ? "<unknown>" : Shiboken::String::toCString(baseNameObj);

                PyErr_Format(PyExc_TypeError,
                    "Class '%s' defines a method '%s' that conflicts with a Signal of the same name "
                    "inherited from '%s'. Methods and Signals cannot share the same name. "
                    "Please rename either the method or the Signal.",
                    className, signalName, baseName);
                return;
            }
        }
    }
}

} // namespace Signal
} // namespace QtBridges
