// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

#ifndef AUTOQMLBRIDGEMODEL_H
#define AUTOQMLBRIDGEMODEL_H

#include <pysideproperty.h>

#include <QtCore/qabstractitemmodel.h>
#include <QtCore/qmetaobject.h>
#include <QtCore/qvariant.h>
#include <QtCore/qhash.h>
#include <QtQml/qqmlparserstatus.h>

namespace QtBridges {

enum class DataType {
    Unknown,
    List,        // List of primitive types (int, str, etc.)
    DataClassList, // List of dataclass objects
    Table
};

class AutoQmlBridgeModel : public QAbstractItemModel
{
    // Q_OBJECT
public:
    AutoQmlBridgeModel(PyObject *backend, const QMetaObject *metaObject, DataType datatype);
    ~AutoQmlBridgeModel();

public:
    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex &index, const QVariant &value, int role = Qt::EditRole) override;
    Qt::ItemFlags flags(const QModelIndex &index) const override;
    QHash<int, QByteArray> roleNames() const override;
    QModelIndex parent(const QModelIndex &child) const override;
    QModelIndex index(int row, int column, const QModelIndex &parent = QModelIndex()) const override;
    const QMetaObject *metaObject() const override;
    void setDynamicMetaObject(const QMetaObject *metaObject);
    int qt_metacall(QMetaObject::Call call, int id, void **args) override;
    void addProperty(int propertyIndex, PySideProperty *property);
    // public wrappers for model updates
    void startInsert(int first, int last);
    void finishInsert();
    void startRemove(int first, int last);
    void finishRemove();
    void startMove(int sourceFirst, int sourceLast, int destinationRow);
    void finishMove();
    void startReset();
    void endReset();

    // Get the Python backend instance
    PyObject *pythonInstance() const { return m_backend; }

    // DataClass support methods
    QStringList getDataClassFieldNames() const;
    void setupDataClassRoles();

    // Emit property change signal by property index
    void emitPropertyChanged(int propertyIndex);

protected:
    // Constructor for subclasses that will set m_backend later
    AutoQmlBridgeModel(const QMetaObject *metaObject, DataType datatype);

    PyObject *m_backend;
    const QMetaObject *m_dynamicMetaObject;
    QHash<int, PySideProperty*> m_propertyMap;
    DataType m_datatype;

    // DataClass support
    QHash<int, QByteArray> m_dataClassRoles;  // Role ID -> Field name mapping
    QStringList m_dataClassFieldNames;        // Cached field names
};

/**
 * Model subclass for Python types registered with bridge_type().
 */
class BridgePyTypeObjectModel : public AutoQmlBridgeModel, public QQmlParserStatus
{
    // Q_OBJECT
    // Q_INTERFACES(QQmlParserStatus)
public:
    // Constructor for QML factory function with explicit Python type
    // used when Python type is passed via userdata in registration
    BridgePyTypeObjectModel(QObject *parent, PyTypeObject *pythonType);

    ~BridgePyTypeObjectModel() override;

    // Get the Python type this model represents
    PyTypeObject *pythonType() const { return m_pythonType; }

    // Override qt_metacast to support QQmlParserStatus interface casting
    // This replaces the functionality normally provided by Q_INTERFACES(QQmlParserStatus)
    void *qt_metacast(const char *classname) override;

    // QQmlParserStatus interface
    void classBegin() override {}
    void componentComplete() override;

private:
    void createPythonInstance();
    void discoverAndRegisterProperties();
    void bindDecoratorsToBackend();
    void callCompleteDecorators();

    PyTypeObject *m_pythonType = nullptr;
    bool m_instanceCreated = false;
};

} // namespace QtBridges

#endif // AUTOQMLBRIDGEMODEL_H
