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

    // Bound signal instance with emit(), connect(), disconnect() methods
    // Created when accessing a Signal descriptor on an instance
    struct QtBridgeSignalInstance {
        PyObject_HEAD
        PyObject *source;             // The Python instance that owns this signal (borrowed ref)
        QByteArray *signature;        // Pre-computed signature: "signalName(type1,type2,...)"
    };

    // Get the Signal type (lazy initialization)
    PyTypeObject *QtBridgeSignal_TypeF();

    // Get the SignalInstance type (lazy initialization)
    PyTypeObject *QtBridgeSignalInstance_TypeF();

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
