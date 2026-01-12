// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef QTBRIDGES_CONVERSION_P_H
#define QTBRIDGES_CONVERSION_P_H

#include <Python.h>
#include <QtCore/qvariant.h>
#include <optional>

QT_FORWARD_DECLARE_CLASS(QByteArray)

namespace QtBridges {

/**
 * Register conversion functions for PyObject <-> QMetaType conversions
 */
int registerPyObjectMetaTypeConversions();

/**
 * Convert Python object to QVariant
 */
std::optional<QVariant> pyObject2VariantOpt(PyObject *obj);

/**
 * Convert QVariant to Python object
 */
PyObject *variant2PyObject(const QVariant &variant);

// Helper functions for specific types
std::optional<QString> pyObject2StringOpt(PyObject *obj);
std::optional<bool> pyObject2BoolOpt(PyObject *obj);

PyObject *variantList2PyObject(const QVariantList &list);
PyObject *variantMap2PyObject(const QVariantMap &map);

/**
 * Convert QVariant containing QJSValue to proper Qt type
 * Handles cases where QML passes QVariant(QJSValue) instead of expected Qt types
 */
QVariant convertQVariantQJSValueToQtType(const QVariant &variantWithJSValue);

} // namespace QtBridges

#endif // QTBRIDGES_CONVERSION_P_H
