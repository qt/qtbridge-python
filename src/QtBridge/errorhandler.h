// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef ERRORHANDLER_H
#define ERRORHANDLER_H

#include <Python.h>

namespace QtBridges {

/**
 * Log Python exception with context-appropriate detail level
 */
void logPythonException(const char *context);

// Main logging function that takes an exception object
void logPythonException(const char *context, PyObject *exc);

/**
 * Check if exception represents a user error (decorator misuse, etc.)
 * These errors should not crash the application eg: uses wrong argument name
 */
bool shouldSuppressError(PyObject *exc);

} // namespace QtBridges

#endif // ERRORHANDLER_H
