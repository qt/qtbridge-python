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

PyObject *CompleteDecoratorPrivate::tp_call(PyObject *self, PyObject *args, PyObject *kwds)
{
    Shiboken::GilState gil;
    if (!validateDecoratorState(this, "complete")) {
        PyErr_SetString(PyExc_RuntimeError, "@complete decorator has no bound backend instance - was bridge_instance() or bridge_type() called?");
        return nullptr;
    }

    // For @complete, we don't need the model - just call the Python method directly
    Shiboken::AutoDecRef bound_method(
        createBoundMethod(this->m_wrapped_func, this->m_backend_instance));
    if (!bound_method) {
        PyErr_SetString(PyExc_RuntimeError, "@complete decorator failed to create bound method");
        return nullptr;
    }

    // Call the wrapped Python method - @complete methods typically take no arguments
    PyObject *result = PyObject_Call(bound_method.object(), args, kwds);

    if (!result) {
        if (PyErr_Occurred()) {
            logPythonException("@complete decorator: Python method call failed");
        }
        return nullptr;
    }

    return result;
}

int CompleteDecoratorPrivate::tp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    if (initDecoratorCommon(self, args, "complete") != 0) {
        return -1;
    }

    PyObject *func;
    PyArg_UnpackTuple(args, "complete", 1, 1, &func);
    Py_INCREF(func);
    this->m_wrapped_func = func;
    return 0;
}

const char *CompleteDecoratorPrivate::name() const
{
    return "complete";
}

} // namespace QtBridges
