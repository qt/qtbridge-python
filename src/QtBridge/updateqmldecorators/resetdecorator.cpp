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

PyObject *ResetDecoratorPrivate::tp_call(PyObject *self, PyObject *args, PyObject *kwds)
{
    Shiboken::GilState gil;
    if (!validateDecoratorState(this, "reset")) {
        logPythonException("@reset - Invalid decorator state");
        return nullptr;
    }

    auto *model = getModelForDecorator(this);
    if (!model) {
        PyErr_SetString(PyExc_RuntimeError,
                        "@reset - Model not found for the bound backend instance. "
                        "Ensure bridge_instance() or bridge_type() was called.");
        logPythonException("@reset - Model not found");
        return nullptr;
    }

    Shiboken::AutoDecRef bound_method(
        createBoundMethod(this->m_wrapped_func, this->m_backend_instance));
    if (!bound_method) {
        return nullptr;
    }

    // Begin model reset
    model->startReset();
    qCDebug(lcQtBridge, "Starting model reset");

    // Call the wrapped Python method
    PyObject *result = PyObject_Call(bound_method.object(), args, kwds);

    // End model reset
    model->endReset();
    qCDebug(lcQtBridge, "Finished model reset");

    if (!result) {
        if (PyErr_Occurred()) {
            logPythonException("@reset decorator: Python method call failed");
        }
        return nullptr;
    }

    return result;
}

int ResetDecoratorPrivate::tp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    if (initDecoratorCommon(self, args, "reset") != 0) {
        return -1;
    }

    PyObject *func{};
    PyArg_UnpackTuple(args, "reset", 1, 1, &func);
    Py_INCREF(func);
    this->m_wrapped_func = func;
    return 0;
}

const char *ResetDecoratorPrivate::name() const
{
    return "reset";
}

} // namespace QtBridges
