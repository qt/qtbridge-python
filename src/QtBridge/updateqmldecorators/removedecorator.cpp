// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "updateqmldecorator_p.h"
#include "decoratorhelpers.h"
#include "../autoqmlbridge_p.h"
#include "../qtbridgelogging_p.h"
#include "../errorhandler.h"

#include <autodecref.h>
#include <gilstate.h>

namespace QtBridges {

PyObject *RemoveDecoratorPrivate::tp_call(PyObject *self, PyObject *args, PyObject *kwds)
{
    Shiboken::GilState gil;
    if (!validateDecoratorState(this, "remove")) {
        logPythonException("@remove - Invalid decorator state");
        return nullptr;
    }

    auto *model = getModelForDecorator(this);
    if (!model) {
        PyErr_SetString(PyExc_RuntimeError,
                        "@remove - Model not found for the bound backend instance. "
                        "Ensure bridge_instance() or bridge_type() was called.");
        logPythonException("@remove - Model not found");
        return nullptr;
    }

    PyObject* index_obj = extractArgumentByName(this->m_wrapped_func, args, kwds, "index");
    if (!index_obj) {
        logPythonException("@remove - Missing index argument in remove decorator");
        return nullptr;
    }

    long rowToRemove = PyLong_AsLong(index_obj);
    if (PyErr_Occurred()) {
        logPythonException(
            "@remove - Failed to convert index argument to long in remove decorator");
        return nullptr;
    }

    model->startRemove(rowToRemove, rowToRemove);
    qCDebug(lcQtBridge, "Starting remove at row: %ld", rowToRemove);

    Shiboken::AutoDecRef bound_method(
        createBoundMethod(this->m_wrapped_func, this->m_backend_instance));
    if (!bound_method) {
        model->finishRemove();
        return nullptr;
    }

    PyObject *result = PyObject_Call(bound_method.object(), args, kwds);
    model->finishRemove();

    if (!result) {
        if (PyErr_Occurred()) {
            logPythonException("@remove - Error in wrapped function");
        }
        return nullptr;
    }

    qCDebug(lcQtBridge, "Finished remove at row: %ld", rowToRemove);
    return result;
}

int RemoveDecoratorPrivate::tp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    if (initDecoratorCommon(self, args, "remove") != 0) {
        return -1;
    }

    // Extract the function
    PyObject *func;
    PyArg_UnpackTuple(args, "remove", 1, 1, &func);

    // Check that an argument named 'index' is present using helper function
    if (!hasArgumentByName(func, "index")) {
        PyErr_SetString(PyExc_TypeError,
                        "@remove-decorated method must have an argument named 'index'");
        return -1;
    }

    Py_XINCREF(func);
    this->m_wrapped_func = func;
    return 0;
}

const char *RemoveDecoratorPrivate::name() const
{
    return "remove";
}

} // namespace QtBridges
