// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef BRIDGESPEP384_H
#define BRIDGESPEP384_H

#include <Python.h>
#include <string>

namespace QtBridges {
namespace Stable {

/**
 * Display Python exception with traceback information.
 * Uses PyErr_DisplayException for Python >= 3.12, falls back to manual formatting for older versions.
 */
std::string formatException(PyObject *exc);

} // namespace Stable
} // namespace QtBridges

#endif // BRIDGESPEP384_H
