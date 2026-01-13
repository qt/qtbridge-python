// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "bridgespep384.h"
#include <sbkstring.h>
#include <sstream>

namespace QtBridges {
namespace Stable {

std::string formatException(PyObject *exc)
{
    if (!exc) {
        return "No exception object provided";
    }

    // Get basic exception info
    PyObject *excType = PyObject_Type(exc);
    std::string typeName;
    if (excType) {
        PyObject *typeNameObj = PyObject_GetAttrString(excType, "__name__");
        if (typeNameObj && PyUnicode_Check(typeNameObj)) {
            typeName = Shiboken::String::toCString(typeNameObj);
        }
        Py_XDECREF(typeNameObj);
        Py_XDECREF(excType);
    }

    PyObject *str = PyObject_Str(exc);
    std::string errorMsg;
    if (str && PyUnicode_Check(str)) {
        errorMsg = Shiboken::String::toCString(str);
    }
    Py_XDECREF(str);

    std::ostringstream result;
    result << typeName << ": " << errorMsg;

#if PY_VERSION_HEX >= 0x030C0000
    // Python >= 3.12: Use PyErr_DisplayException
    // Note: PyErr_DisplayException writes to stderr, so we need to capture it
    // For now, we'll use the fallback approach consistently
    // TODO: Consider implementing stderr capture if needed
#endif

    // Fallback for all Python versions
    PyObject *traceback = PyException_GetTraceback(exc);
    if (traceback && traceback != Py_None) {
        PyObject *tbModule = PyImport_ImportModule("traceback");
        if (tbModule) {
            PyObject *formatTb = PyObject_GetAttrString(tbModule, "format_tb");
            if (formatTb && PyCallable_Check(formatTb)) {
                PyObject *tbLines = PyObject_CallFunctionObjArgs(formatTb, traceback, nullptr);
                if (tbLines && PyList_Check(tbLines)) {
                    result << "\nTraceback:";
                    Py_ssize_t size = PyList_Size(tbLines);
                    for (Py_ssize_t i = 0; i < size; ++i) {
                        PyObject *line = PyList_GetItem(tbLines, i);
                        if (line && PyUnicode_Check(line)) {
                            std::string tbLine = Shiboken::String::toCString(line);
                            // Remove trailing whitespace
                            tbLine.erase(tbLine.find_last_not_of(" \t\r\n") + 1);
                            result << "\n  " << tbLine;
                        }
                    }
                }
                Py_XDECREF(tbLines);
            }
            Py_XDECREF(formatTb);
            Py_XDECREF(tbModule);
        }
    }
    Py_XDECREF(traceback);

    return result.str();
}

} // namespace Stable
} // namespace QtBridges
