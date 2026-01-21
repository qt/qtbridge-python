// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef SIGNAL_P_H
#define SIGNAL_P_H

#include <sbkpython.h>
#include <QtCore/qbytearray.h>

extern "C"
{
    struct QtBridgeSignal {
        PyObject_HEAD
        PyObject *signalName;         // Name of the signal
        PyObject *signatureArgs;      // Tuple of Qt type names for the signal signature
        PyObject *homonymousMethod;   // Optional method with the same name
    };

    // TODO: To be implemented later for bound signal instances with emit(), connect(), disconnect()
    struct QtBridgeSignalInstance;

    // Get the Signal type (lazy initialization)
    PyTypeObject *QtBridgeSignal_TypeF();

}; // extern "C"

namespace QtBridges {
namespace Signal {

// Initialize the Signal type and add it to the module
void init(PyObject *module);

// Check if an object is a QtBridge Signal
bool isSignal(PyObject *obj);

// Get signal name from a Signal instance
const char* getName(PyObject *signalObj);

// Get signal signature arguments
PyObject* getArgs(PyObject *signalObj);

// Get homonymous method if it exists
PyObject* getHomonymousMethod(PyObject *signalObj);

// Build full signal signature for QMetaObjectBuilder, e.g., "error(int,QString)"
// To be used when registering signals in autoqmlbridge.cpp
QByteArray buildSignature(PyObject *signalObj);

} // namespace Signal
} // namespace QtBridges

#endif // SIGNAL_P_H
