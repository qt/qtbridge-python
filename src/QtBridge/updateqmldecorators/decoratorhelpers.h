// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef DECORATORHELPERS_H
#define DECORATORHELPERS_H

#include <sbkpython.h>

namespace QtBridges {

class UpdateQMLDecoratorPrivate;
class AutoQmlBridgeModel;

bool validateDecoratorState(UpdateQMLDecoratorPrivate* decorator, const char* decoratorName);
AutoQmlBridgeModel* getModelForDecorator(UpdateQMLDecoratorPrivate* decorator);
PyObject* createBoundMethod(PyObject* wrapped_func, PyObject* backend_instance);
PyObject* extractArgumentByName(PyObject* wrapped_func, PyObject* args, PyObject* kwds,
                                const char* arg_name, bool is_required = true);
bool hasArgumentByName(PyObject* func, const char* arg_name);
int initDecoratorCommon(PyObject* self, PyObject* args, const char* decorator_name);

} // namespace QtBridges

#endif // DECORATORHELPERS_H
