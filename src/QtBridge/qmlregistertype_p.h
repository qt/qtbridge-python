// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef QMLREGISTERTYPE_P_H
#define QMLREGISTERTYPE_P_H

#include <Python.h>
#include <QtCore/qtyperevision.h>
#include <QtCore/qtconfigmacros.h>

QT_FORWARD_DECLARE_STRUCT(QMetaObject);

namespace QtBridges {

/**
 * Register a BridgePyTypeObjectModel with the QML engine for Python types registered via bridge_type().
 * This function handles the complex QQmlPrivate::RegisterTypeAndRevisions setup and registration.
 */
int registerQmlType(PyTypeObject *pythonType,
                    const QMetaObject *dynamicMetaObject,
                    const char *uri,
                    int versionMajor,
                    int versionMinor,
                    const char *qmlName);

/**
 * QML factory function used internally by the registration system to create the QML type instance.
 */
void createBridgeTypeModel(void *memory, void *userdata);

} // namespace QtBridges

#endif // QMLREGISTERTYPE_P_H
