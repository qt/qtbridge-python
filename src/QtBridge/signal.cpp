// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "signal_p.h"
#include "qtbridgelogging_p.h"
#include "errorhandler.h"

#include <shiboken.h>

#include <QtCore/qbytearray.h>
#include <cstring>

// Forward declaration
namespace QtBridges::Signal {
    QByteArray pythonTypeToQtTypeName(PyObject *type);
    bool isSignal(PyObject *obj);
}

extern "C"
{

static void Signal_dealloc(QtBridgeSignal *self)
{
    Py_XDECREF(self->signalName);
    Py_XDECREF(self->signatureArgs);
    Py_XDECREF(self->homonymousMethod);
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

    // Signal name will be set when __set_name__ is called
    self->signalName = nullptr;

    // Homonymous method will be detected in __set_name__
    self->homonymousMethod = nullptr;

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

    // If there's a homonymous method, get the bound method from the instance
    if (self->homonymousMethod && self->homonymousMethod != Py_None) {
        // Get the bound method directly from the instance using the signal name
        PyObject *boundMethod = PyObject_GetAttr(obj, self->signalName);
        if (!boundMethod) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to get bound method for homonymous method");
            return nullptr;
        }
        return boundMethod;
    }

    // For now, just return the signal itself
    // TODO: return a SignalInstance that supports connect/disconnect
    Py_INCREF(self);
    return reinterpret_cast<PyObject*>(self);
}

// Signal __set_name__ method (called when the signal is assigned to a class attribute)
static PyObject* Signal_set_name(QtBridgeSignal *self, PyObject *args)
{
    PyObject *owner = nullptr;
    PyObject *name = nullptr;

    if (!PyArg_ParseTuple(args, "OO", &owner, &name)) {
        return nullptr;
    }

    if (!PyUnicode_Check(name)) {
        PyErr_SetString(PyExc_TypeError, "Signal name must be a string");
        return nullptr;
    }

    // Store the signal name
    Py_XDECREF(self->signalName);
    Py_INCREF(name);
    self->signalName = name;

    // Check if there's a method with the same name (homonymous method)
    // This allows obj.signalName() to call the method instead of the signal
    if (PyType_Check(owner)) {
        Shiboken::AutoDecRef method(PyObject_GetAttr(owner, name));
        if (method.object() && method.object() != reinterpret_cast<PyObject*>(self)) {
            // Found a different object with the same name - could be a method
            if (PyCallable_Check(method.object()) && !QtBridges::Signal::isSignal(method.object())) {
                qCDebug(lcQtBridge) << "Found homonymous method for signal:"
                                    << Shiboken::String::toCString(name);
                Py_XDECREF(self->homonymousMethod);
                Py_INCREF(method.object());
                self->homonymousMethod = method.object();
            }
        }
        PyErr_Clear(); // Clear any errors from attribute lookup
    }

    qCDebug(lcQtBridge) << "Signal.__set_name__ called with name:"
                        << Shiboken::String::toCString(name);

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

void init(PyObject *module)
{
    auto *signalType = QtBridgeSignal_TypeF();
    if (!signalType) {
        qCWarning(lcQtBridge) << "Failed to create QtBridge.Signal type";
        return;
    }

    Py_INCREF(signalType);
    if (PyModule_AddObject(module, "Signal", reinterpret_cast<PyObject*>(signalType)) < 0) {
        Py_DECREF(signalType);
        qCWarning(lcQtBridge) << "Failed to add QtBridge.Signal to module";
        return;
    }

    qCDebug(lcQtBridge) << "QtBridge.Signal type initialized successfully";
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

PyObject* getHomonymousMethod(PyObject *signalObj)
{
    if (!isSignal(signalObj))
        return nullptr;

    QtBridgeSignal *signal = reinterpret_cast<QtBridgeSignal*>(signalObj);
    if (signal->homonymousMethod && signal->homonymousMethod != Py_None) {
        return signal->homonymousMethod;
    }
    return nullptr;
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

} // namespace Signal
} // namespace QtBridges
