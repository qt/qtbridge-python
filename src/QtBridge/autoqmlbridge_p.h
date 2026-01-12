// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef AUTOQMLBRIDGE_P_H
#define AUTOQMLBRIDGE_P_H

#include "autoqmlbridgemodel_p.h"
#include "pycapsule_p.h"

#include <memory>
#include <dynamicqmetaobject.h>
#include <unordered_map>
#include <sbkpython.h>
#include <QtCore/QObject>

namespace QtBridges {

enum class BridgeMode {
    Instance,  // For bridge_instance() - wrapping existing Python instances
    Type       // For bridge_type() - registering types for QML instantiation
};

class AutoQmlBridgePrivate
{
public:
    // Constructor for instance mode (existing)
    AutoQmlBridgePrivate(PyObject *backend, DataType datatype);

    // Constructor for type mode (new)
    AutoQmlBridgePrivate(PyTypeObject *type);

    // Constructor for type mode with default property
    AutoQmlBridgePrivate(PyTypeObject *type, const QString &defaultProperty);

    static PyObject *bridge_instance(PyObject *self, PyObject *args, PyObject *kwds);
    static PyObject *bridge_type(PyObject *self, PyObject *args, PyObject *kwds);

    AutoQmlBridgeModel* model() const;

    // Registration methods that can be used by both modes
    void registerMethods();
    void registerProperties();
    void registerSignals();

    // Helper methods for initialization
    const QMetaObject *finalizeMetaObject();
    void setBackend(PyObject *backend);

    BridgeMode mode() const { return m_mode; }
    PyTypeObject *pythonType() const { return m_pythonType; }
    PyObject *pythonInstance() const { return m_backend; }

    ~AutoQmlBridgePrivate();

private:
    std::unique_ptr<PySide::MetaObjectBuilder> m_metaObjectBuilder;
    PyObject *m_backend;        // For instance mode
    PyTypeObject *m_pythonType; // For both modes
    std::shared_ptr<AutoQmlBridgeModel> m_model; // Only for instance mode
    BridgeMode m_mode;
    DataType m_datatype;
    QString m_defaultProperty;   // For QML default property

    void setupMetaObjectBuilder();

    // Helper methods that work for both modes
    void registerMethodsFromType(PyTypeObject *type);
    void registerPropertiesFromType(PyTypeObject *type);
    void registerSignalsFromType(PyTypeObject *type);
};

// global map of Python instances to their corresponding QtBridges handler
extern std::unordered_map<PyObject*, std::shared_ptr<AutoQmlBridgePrivate>> s_bridgeMap;

// Global map for tracking Python objects to BridgePyTypeObjectModel instances
// This is used for objects created via bridge_type() and instantiated from QML
extern std::unordered_map<PyObject*, BridgePyTypeObjectModel*> s_typeModelMap;

} // namespace QtBridges

void initAutoQmlBridge(PyObject *module);

#endif // AUTOQMLBRIDGE_P_H
