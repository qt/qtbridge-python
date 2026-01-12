// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "decoratorhelpers.h"
#include "updateqmldecorator_p.h"
#include "../autoqmlbridge_p.h"
#include "../autoqmlbridgemodel_p.h"
#include "../errorhandler.h"
#include "../qtbridgelogging_p.h"

#include <sbkstring.h>

namespace QtBridges {

bool validateDecoratorState(UpdateQMLDecoratorPrivate* decorator, const char* decoratorName)
{
    if (!decorator) {
        PyErr_Format(PyExc_RuntimeError,
                     "Internal error: NULL decorator instance for %s",
                     decoratorName);
        return false;
    }

    if (!decorator->getWrappedFunc()) {
        PyErr_Format(PyExc_ValueError,
                     "@%s decorator was not properly initialized - missing wrapped function",
                     decoratorName);
        return false;
    }

    if (!decorator->getBackendInstance()) {
        PyErr_Format(PyExc_RuntimeError,
                     "@%s decorator has no bound backend instance. "
                     "Decorators must be bound to an instance via bridge_instance() or bridge_type().",
                     decoratorName);
        return false;
    }

    return true;
}

int initDecoratorCommon(PyObject* /*self*/, PyObject* args, const char* decorator_name)
{
    PyObject *func;
    if (!PyArg_UnpackTuple(args, decorator_name, 1, 1, &func)) {
        return -1;
    }

    if (!PyCallable_Check(func)) {
        PyErr_Format(PyExc_TypeError, "@%s can only decorate callable objects, got %s",
                     decorator_name, Py_TYPE(func)->tp_name);
        return -1;
    }

    return 0;
}

AutoQmlBridgeModel* getModelForDecorator(UpdateQMLDecoratorPrivate* decorator)
{
    PyObject* backend = decorator->getBackendInstance();

    if (!backend)
        return nullptr;

    // First check s_bridgeMap (for bridge_instance())
    auto it = s_bridgeMap.find(backend);
    if (it != s_bridgeMap.end()) {
        auto bridge = it->second;
        if (bridge)
            return bridge->model();
    }

    // Then check s_typeModelMap
    // fall back for bridge_type
    auto typeIt = s_typeModelMap.find(backend);
    if (typeIt != s_typeModelMap.end()) {
        qCDebug(lcQtBridge, "getModelForDecorator: Found model in s_typeModelMap for backend %p", backend);
        return typeIt->second;
    }

    qCWarning(lcQtBridge, "getModelForDecorator: Backend instance %p not found in s_bridgeMap or s_typeModelMap", backend);
    return nullptr;
}

PyObject* createBoundMethod(PyObject* wrapped_func, PyObject* backend_instance)
{
    if (!backend_instance) {
        PyErr_SetString(PyExc_RuntimeError,
                        "Cannot create bound method: no backend instance available");
        logPythonException("decoratorhelpers.cpp: no backend instance for bound method");
        return nullptr;
    }

    PyObject* result = PyObject_CallMethod(
        wrapped_func, "__get__", "OO",
        backend_instance,
        (PyObject *)Py_TYPE(backend_instance)
    );

    if (!result) {
        // Python C API should have set an error, but ensure it's set
        if (!PyErr_Occurred()) {
            PyErr_SetString(PyExc_RuntimeError,
                            "Failed to create bound method from decorator");
        }
        logPythonException("decoratorhelpers.cpp: error calling wrapped_func.__get__");
        return nullptr;
    }

    return result;
}

PyObject* extractArgumentByName(PyObject* wrapped_func, PyObject* args, PyObject* kwds,
                                const char* arg_name, bool is_required)
{
    PyObject *code_obj = nullptr;
    if (PyObject_HasAttrString(wrapped_func, "__code__")) {
        code_obj = PyObject_GetAttrString(wrapped_func, "__code__");
    }

    PyObject* result = nullptr;
    if (code_obj) {
        PyObject *varnames = PyObject_GetAttrString(code_obj, "co_varnames");
        PyObject *argcount_obj = PyObject_GetAttrString(code_obj, "co_argcount");
        int argcount = argcount_obj ? (int)PyLong_AsLong(argcount_obj) : 0;

        int arg_pos = -1;
        for (int i = 0; i < argcount; ++i) {
            PyObject *name_obj = PyTuple_GetItem(varnames, i);
            if (!name_obj) continue;
            const char *name = Shiboken::String::toCString(name_obj);
            if (qstrcmp(name, arg_name) == 0) {
                arg_pos = i;
                break;
            }
        }

        // QML/Python calls do not pass 'self', so shift positional mapping by 1
        if (arg_pos >= 1 && (arg_pos - 1) < PyTuple_Size(args)) {
            result = PyTuple_GetItem(args, arg_pos - 1);
        }

        // If not found in positional, check kwds
        if (!result && kwds && PyDict_Check(kwds)) {
            result = PyDict_GetItemString(kwds, arg_name);
        }

        Py_XDECREF(varnames);
        Py_XDECREF(argcount_obj);
        Py_XDECREF(code_obj);
    }

    if (!result && is_required) {
        PyErr_Format(PyExc_ValueError, "Required argument '%s' not found", arg_name);
    }

    return result;
}

bool hasArgumentByName(PyObject* func, const char* arg_name)
{
    PyObject *code_obj = PyObject_GetAttrString(func, "__code__");
    if (!code_obj) return false;

    bool found = false;
    PyObject *varnames = PyObject_GetAttrString(code_obj, "co_varnames");
    PyObject *argcount_obj = PyObject_GetAttrString(code_obj, "co_argcount");

    if (varnames && argcount_obj) {
        int argcount = (int)PyLong_AsLong(argcount_obj);
        for (int i = 0; i < argcount; ++i) {
            PyObject *name_obj = PyTuple_GetItem(varnames, i);
            if (!name_obj) continue;
            const char *name = Shiboken::String::toCString(name_obj);
            if (qstrcmp(name, arg_name) == 0) {
                found = true;
                break;
            }
        }
    }

    Py_XDECREF(varnames);
    Py_XDECREF(argcount_obj);
    Py_XDECREF(code_obj);
    return found;
}

} // namespace QtBridges
