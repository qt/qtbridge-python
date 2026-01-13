// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "updateqmldecorator_p.h"
#include "decoratorhelpers.h"
#include "../autoqmlbridge_p.h"
#include "../qtbridgelogging_p.h"
#include "../errorhandler.h"

#include <autodecref.h>

namespace QtBridges {

PyObject* InsertDecoratorPrivate::tp_call(PyObject* self, PyObject* args, PyObject* kwds)
{
    if (!validateDecoratorState(this, "insert")) {
        logPythonException("@insert - Invalid decorator state");
        return nullptr;
    }

    auto *model = getModelForDecorator(this);
    if (!model) {
        PyErr_SetString(PyExc_RuntimeError,
                        "@insert - Model not found for the bound backend instance. "
                        "Ensure bridge_instance() or bridge_type() was called.");
        logPythonException("@insert - Model not found");
        return nullptr;
    }

    Shiboken::AutoDecRef bound_method(
        createBoundMethod(this->m_wrapped_func, this->m_backend_instance));
    if (!bound_method) {
        return nullptr;
    }

    // fetch 'index' argument, but allow it to be optional for append case
    PyObject* index_obj = extractArgumentByName(
        this->m_wrapped_func, args, kwds, "index", false);

    long index = -1;
    if (index_obj) {
        index = PyLong_AsLong(index_obj);
        if (PyErr_Occurred()) {
            logPythonException("@insert - Failed to convert index argument to long");
            return nullptr;
        }
    } else {
        // append at end
        index = model->rowCount(QModelIndex());
        qCDebug(lcQtBridge, "No index provided to insert; appending at end.");
    }

    model->startInsert(index, index);
    qCDebug(lcQtBridge, "Starting insert at index: %ld", index);

    // Call the original function
    PyObject* result = PyObject_Call(bound_method.object(), args, kwds);

    model->finishInsert();
    if (!result) {
        if (PyErr_Occurred()) {
            logPythonException("@insert - Error in wrapped function");
        }
        return nullptr;
    }

    qCDebug(lcQtBridge, "Finished insert at index: %ld", index);
    return result;
}

int InsertDecoratorPrivate::tp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    if (initDecoratorCommon(self, args, "insert") != 0) {
        return -1;
    }

    PyObject *func{};
    PyArg_UnpackTuple(args, "insert", 1, 1, &func);
    Py_INCREF(func);
    this->m_wrapped_func = func;
    return 0;
}

const char *InsertDecoratorPrivate::name() const
{
    return "insert";
}

} // namespace QtBridges

