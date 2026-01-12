// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "updateqmldecorator_p.h"
#include "decoratorhelpers.h"
#include "../autoqmlbridge_p.h"
#include "../qtbridgelogging_p.h"
#include "../errorhandler.h"

#include <sbktypefactory.h>
#include <signalmanager.h>
#include <autodecref.h>
#include <gilstate.h>

namespace QtBridges {

PyObject *MoveDecoratorPrivate::tp_call(PyObject *self, PyObject *args, PyObject *kwds)
{
    Shiboken::GilState gil;
    if (!validateDecoratorState(this, "move")) {
        logPythonException("@move - Invalid decorator state");
        return nullptr;
    }

    auto model = getModelForDecorator(this);
    if (!model) {
        PyErr_SetString(PyExc_RuntimeError,
                        "@move - Model not found for the bound backend instance. "
                        "Ensure bridge_instance() or bridge_type() was called.");
        logPythonException("@move - Model not found");
        return nullptr;
    }

    PyObject* from_index_obj = extractArgumentByName(
        this->m_wrapped_func, args, kwds, "from_index");
    PyObject* to_index_obj = extractArgumentByName(
        this->m_wrapped_func, args, kwds, "to_index");
    if (!from_index_obj || !to_index_obj) {
        logPythonException(
            "@move - Missing from_index or to_index argument in move decorator");
        return nullptr;
    }

    long fromIndex = PyLong_AsLong(from_index_obj);
    long toIndex = PyLong_AsLong(to_index_obj);
    if (PyErr_Occurred()) {
        logPythonException(
            "@move - Failed to convert from_index or to_index to long in move decorator");
        return nullptr;
    }

    int adjustedToIndex = toIndex;
    if (toIndex > fromIndex) {
        adjustedToIndex++;
    }
    model->startMove(fromIndex, fromIndex, adjustedToIndex);
    qCDebug(lcQtBridge)
        << "Starting move from" << fromIndex << "to" << toIndex
        << ", adjusted to" << adjustedToIndex;

    Shiboken::AutoDecRef bound_method(
        createBoundMethod(this->m_wrapped_func, this->m_backend_instance));
    if (!bound_method) {
        model->finishMove();
        return nullptr;
    }

    PyObject *result = PyObject_Call(bound_method.object(), args, kwds);
    model->finishMove();

    if (!result) {
        if (PyErr_Occurred()) {
            logPythonException("@move - Error in wrapped function");
        }
        return nullptr;
    }

    qCDebug(lcQtBridge)
        << "Finished move from" << fromIndex << "to" << toIndex;
    return result;
}

int MoveDecoratorPrivate::tp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    // Use helper function for validation
    if (initDecoratorCommon(self, args, "move") != 0) {
        return -1;
    }

    // Extract the function
    PyObject *func;
    PyArg_UnpackTuple(args, "move", 1, 1, &func);

    // Check that both 'from_index' and 'to_index' are present using helper functions
    if (!hasArgumentByName(func, "from_index") ||
        !hasArgumentByName(func, "to_index")) {
        PyErr_SetString(
            PyExc_TypeError,
            "@move-decorated method must have 'from_index' and 'to_index' as "
            "parameter names");
        return -1;
    }

    Py_XINCREF(func);
    this->m_wrapped_func = func;
    return 0;
}

const char *MoveDecoratorPrivate::name() const
{
    return "move";
}

} // namespace QtBridges

