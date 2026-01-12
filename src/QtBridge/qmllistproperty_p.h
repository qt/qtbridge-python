// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef QMLLISTPROPERTY_P_H
#define QMLLISTPROPERTY_P_H

#include <sbkpython.h>
#include <pysideproperty_p.h>
#include <QtCore/qobject.h>
#include <QtQml/qqmllist.h>

namespace QtBridges {

class BridgePyTypeObjectModel;

/**
 * Data structure stored in QQmlListProperty to track both the Python list
 * and the property information needed for change signal emission.
 */
struct PyQmlListPropertyData {
    PyObject *pythonList;
    BridgePyTypeObjectModel *owner;
    int propertyIndex; // Index of the property in the model
    const char *propertyName;

    PyQmlListPropertyData(PyObject *list, BridgePyTypeObjectModel *obj, int index, const char *name)
        : pythonList(list), owner(obj), propertyIndex(index), propertyName(name)
    {
        Py_INCREF(pythonList);
    }

    ~PyQmlListPropertyData()
    {
        Py_DECREF(pythonList);
    }
};

/**
 * Custom property class for handling QQmlListProperty in QtBridges.
 * This class automatically creates QQmlListProperty<QObject> for Python list properties
 * that contain QML-registered types, and sets it as the `d` pointer in PySidePropertyPrivate.
 *
 * Unlike PySide6's ListProperty which requires explicit append, count, clear functions,
 * this class automatically manages the Python list internally, so that QML can interact with it
 * seamlessly.
 */
class PyQmlListProperty : public PySidePropertyPrivate
{
public:
    PyQmlListProperty(const PySidePropertyPrivate *original, const char *propertyName = nullptr);
    ~PyQmlListProperty() override = default;

    void metaCall(PyObject *source, QMetaObject::Call call, void **args) override;

private:
    /**
     * Handle reading the property (when QML accesses the list).
     */
    void handleReadProperty(PyObject *source, void **args);

    /**
     * Handle writing to the property (not typically used for QQmlListProperty).
     * Basically raises a warning
     */
    void handleWriteProperty(PyObject *source, void **args);

    // QQmlListProperty callback functions

    /**
     * Called when QML wants to append an object to the list.
     */
    static void appendFunction(QQmlListProperty<QObject> *property, QObject *value);

    /**
     * Called when QML wants to know the count of objects in the list.
     */
    static qsizetype countFunction(QQmlListProperty<QObject> *property);

    /**
     * Called when QML wants to access an object at a specific index.
     */
    static QObject *atFunction(QQmlListProperty<QObject> *property, qsizetype index);

    /**
     * Called when QML wants to clear all objects from the list.
     */
    static void clearFunction(QQmlListProperty<QObject> *property);

private:
    /**
     * Helper method to emit property changed signal after list mutations.
     */
    static void emitListPropertyChanged(PyQmlListPropertyData *data);

private:
    const char *m_propertyName;
};

} // namespace QtBridges

#endif // QMLLISTPROPERTY_P_H
