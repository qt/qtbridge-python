// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#ifndef UPDATEQMLDECORATOR_P_H
#define UPDATEQMLDECORATOR_P_H

#include <pysideclassdecorator_p.h>

namespace QtBridges {

// Abstract base class for all decorators (insert, remove, move, edit)
class UpdateQMLDecoratorPrivate : public PySide::ClassDecorator::DecoratorPrivate
{
public:
    ~UpdateQMLDecoratorPrivate() override;

    PyObject *tp_getattro(PyObject *self, PyObject *name);

    PyObject *getWrappedFunc() const { return m_wrapped_func; }
    PyObject *getBackendInstance() const { return m_backend_instance; }
    void setBackendInstance(PyObject *instance);
protected:
    PyObject *m_wrapped_func = nullptr;
    PyObject *m_backend_instance = nullptr;
};

// Concrete decorator for 'insert'
class InsertDecoratorPrivate : public UpdateQMLDecoratorPrivate
{
public:
    PyObject *tp_call(PyObject *self, PyObject *args, PyObject *kwds) override;
    int tp_init(PyObject *self, PyObject *args, PyObject *kwds) override;
    const char *name() const override;
};

// Concrete decorator for 'remove'
class RemoveDecoratorPrivate : public UpdateQMLDecoratorPrivate
{
public:
    PyObject *tp_call(PyObject *self, PyObject *args, PyObject *kwds) override;
    int tp_init(PyObject *self, PyObject *args, PyObject *kwds) override;
    const char *name() const override;
};

// Concrete decorator for 'move'
class MoveDecoratorPrivate : public UpdateQMLDecoratorPrivate
{
public:
    PyObject *tp_call(PyObject *self, PyObject *args, PyObject *kwds) override;
    int tp_init(PyObject *self, PyObject *args, PyObject *kwds) override;
    const char *name() const override;
};

// Concrete decorator for 'edit'
class EditDecoratorPrivate : public UpdateQMLDecoratorPrivate
{
public:
    PyObject *tp_call(PyObject *self, PyObject *args, PyObject *kwds) override;
    int tp_init(PyObject *self, PyObject *args, PyObject *kwds) override;
    const char *name() const override;
};

// Concrete decorator for 'reset'
class ResetDecoratorPrivate : public UpdateQMLDecoratorPrivate
{
public:
    PyObject *tp_call(PyObject *self, PyObject *args, PyObject *kwds) override;
    int tp_init(PyObject *self, PyObject *args, PyObject *kwds) override;
    const char *name() const override;
};

// Concrete decorator for 'complete'
class CompleteDecoratorPrivate : public UpdateQMLDecoratorPrivate
{
public:
    PyObject *tp_call(PyObject *self, PyObject *args, PyObject *kwds) override;
    int tp_init(PyObject *self, PyObject *args, PyObject *kwds) override;
    const char *name() const override;
};

} // namespace QtBridges

void initInsertDecorator(PyObject *module);
void initRemoveDecorator(PyObject *module);
void initMoveDecorator(PyObject *module);
void initEditDecorator(PyObject *module);
void initResetDecorator(PyObject *module);
void initCompleteDecorator(PyObject *module);

#endif // UPDATEQMLDECORATOR_P_H
