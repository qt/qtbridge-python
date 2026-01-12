// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "autoqmlbridge_p.h"
#include "updateqmldecorators/updateqmldecorator_p.h"

static void cleanupModule()
{
    QtBridges::s_bridgeMap.clear();
}

static PyMethodDef QtBridgesMethods[] = {
    {nullptr, nullptr, 0, nullptr}
};

static PyModuleDef_Slot QtBridgesSlots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(&initAutoQmlBridge)},
    {Py_mod_exec, reinterpret_cast<void*>(&initInsertDecorator)},
    {Py_mod_exec, reinterpret_cast<void*>(&initRemoveDecorator)},
    {Py_mod_exec, reinterpret_cast<void*>(&initMoveDecorator)},
    {Py_mod_exec, reinterpret_cast<void*>(&initEditDecorator)},
    {Py_mod_exec, reinterpret_cast<void*>(&initResetDecorator)},
    {Py_mod_exec, reinterpret_cast<void*>(&initCompleteDecorator)},
    {0, nullptr}  // Sentinel
};

// Define the module
static struct PyModuleDef QtBridgeModule = {
    PyModuleDef_HEAD_INIT,
    "QtBridge",            // m_name
    "QtBridge module",     // m_doc
    0,                     // m_size
    QtBridgesMethods,      // m_methods
    QtBridgesSlots,        // m_slots
    nullptr,              // m_traverse
    nullptr,              // m_clear
    reinterpret_cast<freefunc>(&cleanupModule)  // m_free
};

PyMODINIT_FUNC PyInit_QtBridge(void)
{
    return PyModuleDef_Init(&QtBridgeModule);
}
