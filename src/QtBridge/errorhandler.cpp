// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "errorhandler.h"
#include "qtbridgelogging_p.h"
#include "bridgespep384.h"
#include <pep384impl.h>
#include <sbkerrors.h>
#include <sbkstring.h>
#include <string>

namespace QtBridges {

void logPythonException(const char *context, PyObject *exc)
{
    std::string msg = context ? context : "Python error";

    if (exc) {
        bool isUserError = shouldSuppressError(exc);
#ifdef DEBUG_BUILD
        // In debug builds, with debug logging level as default
        std::string formattedException = QtBridges::Stable::formatException(exc);
        msg += ": " + formattedException;
        if (isUserError) {
            qCWarning(lcQtBridge, "%s", msg.c_str());
        } else {
            qCCritical(lcQtBridge, "%s", msg.c_str());
        }
#else
        // In runtime with Warning logging level
        PyObject *str = PyObject_Str(exc);
        std::string errorMsg = "";
        if (str && PyUnicode_Check(str)) {
            errorMsg = Shiboken::String::toCString(str);
        }
        Py_XDECREF(str);
        if (isUserError) {
            msg += ": " + errorMsg;
            qCWarning(lcQtBridge, "%s", msg.c_str());
        } else {
            // For runtime/system errors, show more detail
            PyObject *excType = PyObject_Type(exc);
            std::string typeName = "";
            if (excType) {
                PyObject *typeNameObj = PyObject_GetAttrString(excType, "__name__");
                if (typeNameObj && PyUnicode_Check(typeNameObj)) {
                    typeName = Shiboken::String::toCString(typeNameObj);
                }
                Py_XDECREF(typeNameObj);
                Py_XDECREF(excType);
            }
            msg += ": " + typeName + ": " + errorMsg;
            qCCritical(lcQtBridge, "%s", msg.c_str());
        }
#endif
    }

    // we do not want to clear the error here but rather let the caller/user handle it.
    // therefore, we propagate the error state as is. The reseting of the error state
    // is actually done inside PepErr_GetRaisedException when needed.

}

void logPythonException(const char *context)
{
    if (PyObject *exc = PyErr_Occurred()) {
        Shiboken::Errors::Stash stash;
        logPythonException(context, stash.getException());
    } else {
        qCWarning(lcQtBridge, "logPythonException: No Python error occurred");
    }
}

bool shouldSuppressError(PyObject *exc)
{
    if (!exc) return false;

    // User errors - decorator misuse, invalid arguments names, etc.
    return PyErr_GivenExceptionMatches(exc, PyExc_IndexError) ||
           PyErr_GivenExceptionMatches(exc, PyExc_ValueError) ||
           PyErr_GivenExceptionMatches(exc, PyExc_TypeError) ||
           PyErr_GivenExceptionMatches(exc, PyExc_AttributeError) ||
           PyErr_GivenExceptionMatches(exc, PyExc_KeyError);
}


} // namespace QtBridges
