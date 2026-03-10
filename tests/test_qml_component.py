# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

"""Tests for load_qml_component / QmlComponentFactory / QmlObject."""

import sys
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from QtBridge.qtbridge_py.qml_component import load_qml_component

PERSON_QML = """\
import QtQuick

QtObject {
    property string name: "John"
    property int age: 30
    signal birthdayHappened()
    function celebrateBirthday() {
        age++
        birthdayHappened()
    }
}
"""

SIMPLE_QML = """\
import QtQuick

QtObject {
    property string greeting: "hello"
}
"""

VAR_PROPS_QML = """\
import QtQuick

QtObject {
    property var items: []
    property var metadata: ({})
}
"""

# TODO: Use fixtures for the other tests as well
@pytest.fixture(scope="session")
def app():
    """Ensure a QGuiApplication exists for the test session."""
    instance = QGuiApplication.instance()
    if instance is None:
        instance = QGuiApplication(sys.argv)
    return instance


@pytest.fixture()
def qml_engine(app):
    """Provide a QQmlApplicationEngine and patch the qtbridge module-level
    ``_engine`` so that ``get_engine()`` returns it."""
    import QtBridge.qtbridge_py.qtbridge as _mod

    engine = QQmlApplicationEngine()
    old = _mod._engine
    _mod._engine = engine
    yield engine
    _mod._engine = old
    del engine


@pytest.fixture()
def person_qml(tmp_path: Path) -> Path:
    """Write person.qml into a temp directory and return the file path."""
    p = tmp_path / "person.qml"
    p.write_text(PERSON_QML)
    return p


@pytest.fixture()
def simple_qml(tmp_path: Path) -> Path:
    p = tmp_path / "simple.qml"
    p.write_text(SIMPLE_QML)
    return p


@pytest.fixture()
def var_props_qml(tmp_path: Path) -> Path:
    p = tmp_path / "var_props.qml"
    p.write_text(VAR_PROPS_QML)
    return p


class TestLoadQmlComponent:
    """Tests for the load_qml_component() factory function."""

    def test_returns_factory_for_file(self, person_qml: Path):
        factory = load_qml_component(str(person_qml))
        assert factory is not None
        assert "person.qml" in repr(factory)

    def test_returns_factory_for_module(self):
        factory = load_qml_component(module="QtQuick", type_name="QtObject")
        assert factory is not None
        assert "QtQuick" in repr(factory)

    def test_raises_without_args(self):
        with pytest.raises(ValueError, match="requires either"):
            load_qml_component()

    def test_create_raises_without_engine(self, person_qml: Path):
        """create() must fail when no @qtbridge engine is running."""
        import QtBridge.qtbridge_py.qtbridge as _mod

        old = _mod._engine
        _mod._engine = None
        try:
            factory = load_qml_component(str(person_qml))
            with pytest.raises(RuntimeError, match="No QQmlApplicationEngine"):
                factory.create()
        finally:
            _mod._engine = old

class TestQmlObjectProperties:
    """Test property read/write on QmlObject wrappers."""

    def test_read_default_properties(self, qml_engine, person_qml: Path):
        Person = load_qml_component(str(person_qml))
        person = Person.create()

        assert person.name == "John"
        assert person.age == 30

    def test_write_properties(self, qml_engine, person_qml: Path):
        Person = load_qml_component(str(person_qml))
        person = Person.create()

        person.name = "Alice"
        person.age = 25

        assert person.name == "Alice"
        assert person.age == 25

    def test_create_with_initial_properties(self, qml_engine, person_qml: Path):
        Person = load_qml_component(str(person_qml))
        person = Person.create(name="Bob", age=42)

        assert person.name == "Bob"
        assert person.age == 42

    def test_qobject_escape_hatch(self, qml_engine, simple_qml: Path):
        factory = load_qml_component(str(simple_qml))
        obj = factory.create()

        # The underlying QObject should be accessible
        qobj = obj.qobject
        assert qobj is not None
        assert qobj.property("greeting") == "hello"

class TestQmlObjectSignals:
    """Test signal connection and emission through QmlObject."""

    def test_signal_connect_and_emit(self, qml_engine, person_qml: Path):
        Person = load_qml_component(str(person_qml))
        person = Person.create()

        callback_called = []

        def on_birthday():
            callback_called.append(True)

        person.birthdayHappened.connect(on_birthday)
        person.celebrateBirthday()

        assert len(callback_called) == 1
        assert person.age == 31  # age was 30, incremented by celebrateBirthday

    def test_signal_fires_multiple_times(self, qml_engine, person_qml: Path):
        Person = load_qml_component(str(person_qml))
        person = Person.create(age=20)

        count = []

        person.birthdayHappened.connect(lambda: count.append(1))
        person.celebrateBirthday()
        person.celebrateBirthday()
        person.celebrateBirthday()

        assert len(count) == 3
        assert person.age == 23


class TestQmlObjectMethods:
    """Test calling QML-defined functions from Python."""

    def test_call_qml_function(self, qml_engine, person_qml: Path):
        Person = load_qml_component(str(person_qml))
        person = Person.create(age=50)

        person.celebrateBirthday()
        assert person.age == 51

    def test_repr(self, qml_engine, simple_qml: Path):
        factory = load_qml_component(str(simple_qml))
        obj = factory.create()
        r = repr(obj)
        assert "QmlObject" in r

class TestQmlComponentErrors:
    """Test error paths."""

    def test_invalid_file_raises(self, qml_engine, tmp_path: Path):
        factory = load_qml_component(str(tmp_path / "nonexistent.qml"))
        with pytest.raises(RuntimeError, match="Failed to load"):
            factory.create()

    def test_malformed_qml_raises(self, qml_engine, tmp_path: Path):
        bad_qml = tmp_path / "bad.qml"
        bad_qml.write_text("this is not valid QML {{{")

        factory = load_qml_component(str(bad_qml))
        with pytest.raises(RuntimeError):
            factory.create()

    def test_unknown_attribute_raises(self, qml_engine, simple_qml: Path):
        factory = load_qml_component(str(simple_qml))
        obj = factory.create()
        with pytest.raises(AttributeError, match="no_such_thing"):
            _ = obj.no_such_thing

    def test_python_only_attribute(self, qml_engine, simple_qml: Path):
        """Underscore-prefixed or unknown attrs are stored on the wrapper."""
        factory = load_qml_component(str(simple_qml))
        obj = factory.create()
        obj._custom = 42
        assert obj._custom == 42


class TestQmlObjectVariantProperties:
    """Test assigning Python lists and dicts to QML 'property var' properties.
    """

    def test_assign_list_of_ints(self, qml_engine, var_props_qml: Path):
        obj = load_qml_component(str(var_props_qml)).create()
        obj.items = [1, 2, 3]
        result = obj.items
        assert list(result) == [1, 2, 3]

    def test_assign_list_of_strings(self, qml_engine, var_props_qml: Path):
        obj = load_qml_component(str(var_props_qml)).create()
        obj.items = ["a", "b", "c"]
        result = obj.items
        assert list(result) == ["a", "b", "c"]

    def test_assign_mixed_list(self, qml_engine, var_props_qml: Path):
        obj = load_qml_component(str(var_props_qml)).create()
        obj.items = [1, "two", 3.0, True]
        result = obj.items
        assert list(result) == [1, "two", 3.0, True]

    def test_assign_empty_list(self, qml_engine, var_props_qml: Path):
        obj = load_qml_component(str(var_props_qml)).create()
        obj.items = []
        result = obj.items
        assert list(result) == []

    def test_assign_dict(self, qml_engine, var_props_qml: Path):
        obj = load_qml_component(str(var_props_qml)).create()
        obj.metadata = {"key": "value", "count": 42}
        result = obj.metadata
        assert result["key"] == "value"
        assert result["count"] == 42

    def test_assign_empty_dict(self, qml_engine, var_props_qml: Path):
        obj = load_qml_component(str(var_props_qml)).create()
        obj.metadata = {}
        result = obj.metadata
        assert dict(result) == {}

    def test_reassign_list(self, qml_engine, var_props_qml: Path):
        """Verify that re-assigning a list property replaces the value."""
        obj = load_qml_component(str(var_props_qml)).create()
        obj.items = [10, 20]
        obj.items = [30, 40, 50]
        assert list(obj.items) == [30, 40, 50]

    def test_reassign_dict(self, qml_engine, var_props_qml: Path):
        """Verify that re-assigning a dict property replaces the value."""
        obj = load_qml_component(str(var_props_qml)).create()
        obj.metadata = {"x": 1}
        obj.metadata = {"y": 2, "z": 3}
        result = obj.metadata
        assert "x" not in result
        assert result["y"] == 2
        assert result["z"] == 3
