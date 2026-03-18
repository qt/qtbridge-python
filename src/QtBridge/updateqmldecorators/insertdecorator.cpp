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
    // Parameterized decorator — func not yet stored, receive it now
    if (!this->m_wrapped_func) {
        PyObject *func{};
        if (!PyArg_UnpackTuple(args, "insert", 1, 1, &func))
            return nullptr;

        if (!PyCallable_Check(func)) {
            PyErr_Format(PyExc_TypeError, "@insert can only decorate callable objects, got %s",
                         Py_TYPE(func)->tp_name);
            return nullptr;
        }
        Py_INCREF(func);
        this->m_wrapped_func = func;
        Py_INCREF(self);
        return self;
    }

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
        index = m_col ? model->columnCount() : model->rowCount();
        qCDebug(lcQtBridge, "No index provided to insert; appending at end.");
    }

    m_col ? model->startInsertCol(index, index) : model->startInsert(index, index);

    qCDebug(lcQtBridge, "Starting insert at index: %ld", index);

    // Call the original function
    PyObject* result = PyObject_Call(bound_method.object(), args, kwds);

    m_col ? model->finishInsertCol() : model->finishInsert();

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
    static char col_kw[] = "col";
    static char *keywords[] = {col_kw, nullptr};
    int col = 0; // Default is false

    const int initResult = initDecoratorCommon(self, args, "insert");

    if (initResult < 0)
        return -1;
    else if (initResult == 1)
        PyArg_ParseTupleAndKeywords(args, kwds, "|p", keywords, &col);

    this->m_col = col;

    PyObject *func{};
    PyArg_UnpackTuple(args, "insert", 0, 1, &func);

    if (func) {
        Py_INCREF(func);
        this->m_wrapped_func = func;
    }
    return 0;
}

const char *InsertDecoratorPrivate::name() const
{
    return "insert";
}

} // namespace QtBridges

