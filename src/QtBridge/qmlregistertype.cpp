// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "qmlregistertype_p.h"
#include "autoqmlbridgemodel_p.h"
#include "qtbridgelogging_p.h"

#include <QtQml/qqmlprivate.h>
#include <QtQml/qqmllist.h>
#include <QtQml/qqmlparserstatus.h>
#include <QtQml/qqmlpropertyvaluesource.h>
#include <QtCore/qmetatype.h>
#include <QtCore/qmetaobject.h>
#include <QtCore/qthread.h>
#include <pep384impl.h>
#include <private/qqmlmetatype_p.h>

namespace {
    // Add the custom parser factory function like PySide6 does
    QQmlCustomParser *defaultCustomParserFactory()
    {
        return nullptr;
    }

}

namespace QtBridges {

void createBridgeTypeModel(void *memory, void *userdata)
{
    Q_ASSERT(memory);
    Q_ASSERT(userdata);

    // userdata contains the PyTypeObject* from registration
    auto *pythonType = static_cast<PyTypeObject*>(userdata);

    if (!pythonType) {
        qCWarning(lcQtBridge, "createBridgeTypeModel called with null Python type!");
        return;
    }

    qCDebug(lcQtBridge, "createBridgeTypeModel: Creating BridgePyTypeObjectModel for type: %s at memory: %p",
            pythonType->tp_name, memory);

    try {
        auto *obj = new (memory) BridgePyTypeObjectModel(nullptr, pythonType);

        if (obj) {
            // The object was created in QML-managed memory, so it's automatically QML-owned
            qCDebug(lcQtBridge,
                "createBridgeTypeModel: Successfully created BridgePyTypeObjectModel at %p for type: %s (memory: %p, QML-owned)",
                obj, pythonType->tp_name, memory);

            // Verify that we can cast to QQmlParserStatus
            auto *parserStatus = static_cast<QQmlParserStatus*>(obj);
            qCDebug(lcQtBridge, "createBridgeTypeModel: Cast to QQmlParserStatus: %p (offset: %td bytes)",
                    parserStatus, reinterpret_cast<char*>(parserStatus) - reinterpret_cast<char*>(obj));
        }
    } catch (const std::exception& e) {
        qCWarning(lcQtBridge, "Exception creating BridgePyTypeObjectModel for type %s: %s",
                 pythonType->tp_name, e.what());
    } catch (...) {
        qCWarning(lcQtBridge, "Unknown exception creating BridgePyTypeObjectModel for type: %s",
                 pythonType->tp_name);
    }
}

int registerQmlType(PyTypeObject *pythonType,
                    const QMetaObject *dynamicMetaObject,
                    const char *uri,
                    int versionMajor,
                    int versionMinor,
                    const char *qmlName)
{
    Q_ASSERT(uri && dynamicMetaObject && qmlName);
    Q_ASSERT(versionMajor >= 0 && versionMinor >= 0);

    qCDebug(lcQtBridge, "Registering QML type '%s' from uri '%s' v%d.%d",
            qmlName, uri, versionMajor, versionMinor);

    // Increment reference count for Python type
    if (pythonType) {
        Py_XINCREF(pythonType);
    }

    // Set up meta types using the Python class name for QML registration
    // The actual C++ type is BridgePyTypeObjectModel, but QML sees it as the Python class name
    const QByteArray qmlTypeName(qmlName);
    const QMetaType typeMetaType(new QQmlMetaTypeInterface(qmlTypeName + '*'));
    const QMetaType listMetaType(new QQmlListMetaTypeInterface(
        QByteArrayLiteral("QQmlListProperty<") + qmlTypeName + '>', typeMetaType.iface()));

    QList<int> qmlTypeIds;

    // Calculate the parser status cast offset
    const int parserStatusCastValue = QQmlPrivate::StaticCastSelector<QtBridges::BridgePyTypeObjectModel, QQmlParserStatus>::cast();
    qCDebug(lcQtBridge, "registerQmlType: parserStatusCast offset calculated: %d", parserStatusCastValue);
    qCDebug(lcQtBridge, "registerQmlType: BridgePyTypeObjectModel size: %zu, inherits QQmlParserStatus: %s",
            sizeof(QtBridges::BridgePyTypeObjectModel),
            std::is_base_of<QQmlParserStatus, QtBridges::BridgePyTypeObjectModel>::value ? "yes" : "no");

    // Set up the registration structure
    QQmlPrivate::RegisterTypeAndRevisions registration = {
        .structVersion = QQmlPrivate::RegisterType::StructVersion::Base,
        .typeId = typeMetaType,
        .listId = listMetaType,
        .objectSize = sizeof(QtBridges::BridgePyTypeObjectModel),
        .create = createBridgeTypeModel,
        .userdata = pythonType,
        .createValueType = {},
        .uri = uri,
        .version = QTypeRevision::fromVersion(versionMajor, versionMinor),
        .metaObject = dynamicMetaObject,
        .classInfoMetaObject = dynamicMetaObject,
        .attachedPropertiesFunction = nullptr,
        .attachedPropertiesMetaObject = nullptr,
        .parserStatusCast = parserStatusCastValue,
        .valueSourceCast = QQmlPrivate::StaticCastSelector<QObject, QQmlPropertyValueSource>::cast(),
        .valueInterceptorCast = QQmlPrivate::StaticCastSelector<QObject, QQmlPropertyValueInterceptor>::cast(),
        .extensionObjectCreate = nullptr,
        .extensionMetaObject = nullptr,
        .customParserFactory = defaultCustomParserFactory,
        .qmlTypeIds = &qmlTypeIds,
        .finalizerCast = 0,
        .forceAnonymous = false,
        .listMetaSequence = {}
    };

    QQmlPrivate::qmlregister(QQmlPrivate::TypeAndRevisionsRegistration, &registration);

    const int qmlTypeId = qmlTypeIds.value(0, -1);
    if (qmlTypeId == -1) {
        qCWarning(lcQtBridge, "QML registration failed for type '%s'", qmlName);
        if (pythonType) {
            Py_XDECREF(pythonType);
        }
    } else {
        qCDebug(lcQtBridge, "Successfully registered QML type '%s' with ID %d", qmlName, qmlTypeId);
    }

    return qmlTypeId;
}

} // namespace QtBridges
