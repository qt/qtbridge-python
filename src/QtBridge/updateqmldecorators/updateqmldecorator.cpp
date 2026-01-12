// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

#include "updateqmldecorator_p.h"
#include "../autoqmlbridge_p.h"
#include "decoratorhelpers.h"

#include <sbkstring.h>
#include <sbktypefactory.h>

namespace {

PyObject *decorator_tp_getattro(PyObject *self, PyObject *name)
{
    auto *decorator = reinterpret_cast<PySideClassDecorator *>(self);
    auto *updateDecorator = static_cast<QtBridges::UpdateQMLDecoratorPrivate *>(decorator->d);
    return updateDecorator->tp_getattro(self, name);
}

template <typename DecoratorPrivate>
PyType_Slot *makeDecoratorTypeSlots()
{
    static PyType_Slot typeSlots[] = {
        {Py_tp_call,
         reinterpret_cast<void *>(
             PySide::ClassDecorator::Methods<DecoratorPrivate>::tp_call)},
        {Py_tp_init,
         reinterpret_cast<void *>(
             PySide::ClassDecorator::Methods<DecoratorPrivate>::tp_init)},
        {Py_tp_new,
         reinterpret_cast<void *>(
             PySide::ClassDecorator::Methods<DecoratorPrivate>::tp_new)},
        {Py_tp_free,
         reinterpret_cast<void *>(
             PySide::ClassDecorator::Methods<DecoratorPrivate>::tp_free)},
        {Py_tp_dealloc, reinterpret_cast<void *>(Sbk_object_dealloc)},
        {Py_tp_getattro, reinterpret_cast<void *>(decorator_tp_getattro)},
        {0, nullptr}
    };
    return typeSlots;
}

} // anonymous namespace

namespace QtBridges {

UpdateQMLDecoratorPrivate::~UpdateQMLDecoratorPrivate()
{
    Py_XDECREF(m_wrapped_func);
    Py_XDECREF(m_backend_instance);
}

void UpdateQMLDecoratorPrivate::setBackendInstance(PyObject *instance)
{
    Py_XINCREF(instance);
    Py_XDECREF(m_backend_instance);
    m_backend_instance = instance;
}

PyObject *UpdateQMLDecoratorPrivate::tp_getattro(PyObject *self, PyObject *name)
{
    // this is needed to return the attributes of the wrapped_func when
    // registering the methods as slots, in order to properly identify the
    // annotations
    if (m_wrapped_func && PyUnicode_Check(name)) {
    const char *attr_name = Shiboken::String::toCString(name);
    if (attr_name && (qstrcmp(attr_name, "__annotations__") == 0 ||
              qstrcmp(attr_name, "__name__") == 0 ||
              qstrcmp(attr_name, "__doc__") == 0 ||
              qstrcmp(attr_name, "__module__") == 0 ||
              qstrcmp(attr_name, "__qualname__") == 0)) {
            if (PyObject_HasAttr(m_wrapped_func, name)) {
                return PyObject_GetAttr(m_wrapped_func, name);
            }
        }
    }

    // Fall back to default attribute access
    return PyObject_GenericGetAttr(self, name);
}

} // namespace QtBridges

extern "C" {

static PyTypeObject *createInsertType()
{
    PyType_Spec spec = {
        "2:QtBridges.insert",
        sizeof(PySideClassDecorator),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VERSION_TAG,
        makeDecoratorTypeSlots<QtBridges::InsertDecoratorPrivate>()
    };
    return SbkType_FromSpec(&spec);
}

PyTypeObject *Insert_TypeF(void)
{
    static auto *type = createInsertType();
    return type;
}

static PyTypeObject *createRemoveType()
{
    PyType_Spec spec = {
        "2:QtBridges.remove",
        sizeof(PySideClassDecorator),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VERSION_TAG,
        makeDecoratorTypeSlots<QtBridges::RemoveDecoratorPrivate>()
    };
    return SbkType_FromSpec(&spec);
}

PyTypeObject *Remove_TypeF(void)
{
    static auto *type = createRemoveType();
    return type;
}

static PyTypeObject *createMoveType()
{
    PyType_Spec spec = {
        "2:QtBridges.move",
        sizeof(PySideClassDecorator),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VERSION_TAG,
        makeDecoratorTypeSlots<QtBridges::MoveDecoratorPrivate>()
    };
    return SbkType_FromSpec(&spec);
}

PyTypeObject *Move_TypeF(void)
{
    static auto *type = createMoveType();
    return type;
}

static PyTypeObject *createEditType()
{
    PyType_Spec spec = {
        "2:QtBridges.edit",
        sizeof(PySideClassDecorator),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VERSION_TAG,
        makeDecoratorTypeSlots<QtBridges::EditDecoratorPrivate>()
    };
    return SbkType_FromSpec(&spec);
}

PyTypeObject *Edit_TypeF(void)
{
    static auto *type = createEditType();
    return type;
}

static PyTypeObject *createResetType()
{
    PyType_Spec spec = {
        "2:QtBridges.reset",
        sizeof(PySideClassDecorator),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VERSION_TAG,
        makeDecoratorTypeSlots<QtBridges::ResetDecoratorPrivate>()
    };
    return SbkType_FromSpec(&spec);
}

PyTypeObject *Reset_TypeF(void)
{
    static auto *type = createResetType();
    return type;
}

static PyTypeObject *createCompleteType()
{
    PyType_Spec spec = {
        "2:QtBridges.complete",
        sizeof(PySideClassDecorator),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VERSION_TAG,
        makeDecoratorTypeSlots<QtBridges::CompleteDecoratorPrivate>()
    };
    return SbkType_FromSpec(&spec);
}

PyTypeObject *Complete_TypeF(void)
{
    static auto *type = createCompleteType();
    return type;
}
}

void initInsertDecorator(PyObject *module)
{
    Py_XINCREF(Insert_TypeF());
    PyModule_AddObject(module, "insert", reinterpret_cast<PyObject *>(Insert_TypeF()));
}

void initRemoveDecorator(PyObject *module)
{
    Py_XINCREF(Remove_TypeF());
    PyModule_AddObject(module, "remove", reinterpret_cast<PyObject *>(Remove_TypeF()));
}

void initMoveDecorator(PyObject *module)
{
    Py_XINCREF(Move_TypeF());
    PyModule_AddObject(module, "move", reinterpret_cast<PyObject *>(Move_TypeF()));
}

void initEditDecorator(PyObject *module)
{
    auto *type = Edit_TypeF();
    if (PyModule_AddObject(module, "edit", reinterpret_cast<PyObject *>(type)) < 0) {
        PyErr_Print();
    }
}

void initResetDecorator(PyObject *module)
{
    Py_XINCREF(Reset_TypeF());
    PyModule_AddObject(module, "reset", reinterpret_cast<PyObject *>(Reset_TypeF()));
}

void initCompleteDecorator(PyObject *module)
{
    Py_XINCREF(Complete_TypeF());
    PyModule_AddObject(module, "complete", reinterpret_cast<PyObject *>(Complete_TypeF()));
}
