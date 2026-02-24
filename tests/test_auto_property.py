# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

"""
Tests for the automatic property generation feature.

Run with:
    QT_LOGGING_RULES="qtbridges.debug=true" QTBRIDGE_DEBUG=1 pytest tests/test_auto_property.py -v
"""

import sys
import pytest
from pathlib import Path
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, bridge_type, Signal
def _load_qml(engine, tmp_path, qml_content, qtbot):
    """Write QML to a temp file, load it, and wait until root objects appear."""
    qml_file = tmp_path / "test.qml"
    qml_file.write_text(qml_content)
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    qtbot.waitUntil(lambda: bool(engine.rootObjects()), timeout=5000)
    return engine.rootObjects()[0]


class TestAutoPropertyBridgeInstance:
    """Auto-property generation via bridge_instance()."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured = []
        qInstallMessageHandler(lambda t, c, m: self.captured.append(m))

    def teardown_method(self):
        if self.engine is not None:
            del self.engine
            self.engine = None
        qInstallMessageHandler(None)
        self.captured.clear()

    def test_plain_attribute_becomes_property(self, qtbot, tmp_path: Path):
        """
        An instance attribute assigned in __init__ should become a QML property
        with the same name, readable from QML.
        """
        class _SimpleModel:
            def __init__(self):
                self.count = 0
                self.label = "hello"


        obj = _SimpleModel()
        bridge_instance(obj, name="SimpleModel")

        qml = """
import QtQuick 2.0
import backend 1.0
Item {
    Component.onCompleted: {
        console.log("count:", SimpleModel.count)
        console.log("label:", SimpleModel.label)
    }
}
"""
        _load_qml(self.engine, tmp_path, qml, qtbot)

        assert any("count: 0" in m for m in self.captured), self.captured
        assert any("label: hello" in m for m in self.captured), self.captured

    def test_property_value_survives_augmentation(self, qtbot, tmp_path):
        """When the object is created before bridge_instance is called the
        already-assigned value must survive the descriptor creation step."""

        class DataModel:
            def __init__(self, value):
                self.score = value

        obj = DataModel(42)
        bridge_instance(obj, name="DataModel")

        # Access through the newly-installed property descriptor
        assert obj.score == 42

    def test_setter_updates_value(self, qtbot, tmp_path):
        """Writing to an auto-property from QML should call the setter and
        update the backing field."""

        class MutableModel:
            def __init__(self):
                self.value = 10

        obj = MutableModel()
        bridge_instance(obj, name="MutableModel")

        qml = """
import QtQuick 2.0
import backend 1.0
Item {
    Component.onCompleted: {
        MutableModel.value = 99
        console.log("after set:", MutableModel.value)
    }
}
"""
        _load_qml(self.engine, tmp_path, qml, qtbot)
        assert obj.value == 99

    def test_change_signal_emitted(self, qtbot, tmp_path):
        """The auto-generated *Changed signal should fire when the property
        value changes, and QML listeners should be notified."""

        class ObservableModel:
            def __init__(self):
                self.score = 0

        obj = ObservableModel()
        bridge_instance(obj, name="ObservableModel")

        # Verify the signal descriptor was added to the class
        assert hasattr(type(obj), "scoreChanged")

        qml = """
import QtQuick 2.0
import backend 1.0
Item {
    property int received: 0
    Component.onCompleted: {
        ObservableModel.scoreChanged.connect(function() {
            received++
            console.log("signal received, score:", ObservableModel.score)
        })
        ObservableModel.score = 7
        ObservableModel.score = 7  // duplicate — should NOT fire again
        ObservableModel.score = 8
    }
}
"""
        root = _load_qml(self.engine, tmp_path, qml, qtbot)
        print(self.captured)
        # signal should have fired twice
        assert root.property("received") == 2

    def test_underscore_attributes_ignored(self, qtbot, tmp_path):
        """Private attributes (self._x) must NOT generate auto-properties."""

        class PrivateModel:
            def __init__(self):
                self._secret = 99
                self.public = 1

        obj = PrivateModel()
        bridge_instance(obj, name="PrivateModel")

        # _secret should remain a plain instance attribute, not a property
        assert not isinstance(type(obj).__dict__.get("_secret"), property)
        assert not hasattr(type(obj), "_secretChanged")
        # public should be a property
        assert isinstance(type(obj).__dict__.get("public"), property)

    def test_exclude_properties_param(self, qtbot, tmp_path):
        """Attributes listed in exclude_properties must be skipped."""

        class FilteredModel:
            def __init__(self):
                self.name = "keep"
                self.internal = "skip"

        obj = FilteredModel()
        bridge_instance(obj, name="FilteredModel", exclude_properties={"internal"})

        assert isinstance(type(obj).__dict__.get("name"), property)
        assert not isinstance(type(obj).__dict__.get("internal"), property)

    def test_multiple_instances_share_augmentation(self, qtbot, tmp_path):
        """Augmentation runs only once per class regardless of how many
        instances are bridged (_qtbridge_auto_props_applied marker)."""

        class SharedModel:
            def __init__(self, x):
                self.x = x

        obj1 = SharedModel(1)
        obj2 = SharedModel(2)

        bridge_instance(obj1, name="Shared1")
        bridge_instance(obj2, name="Shared2")

        assert obj1.x == 1
        assert obj2.x == 2
        assert type(obj1) is type(obj2)
        assert hasattr(type(obj1), "_qtbridge_auto_props_applied")

class TestAutoPropertyBridgeType:
    """Auto-property generation via bridge_type()."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured = []
        qInstallMessageHandler(lambda t, c, m: self.captured.append(m))

    def teardown_method(self):
        del self.engine
        self.engine = None
        qInstallMessageHandler(None)
        self.captured.clear()

    def test_plain_attr_readable_from_qml(self, qtbot, tmp_path):
        """A class registered with bridge_type() should expose plain __init__
        attributes as QML properties."""

        class Widget:
            def __init__(self):
                self.width = 100
                self.title = "default"

        bridge_type(Widget, uri="AutoPropTestBackend", version="1.0")

        qml = """
import QtQuick 2.0
import AutoPropTestBackend 1.0
Item {
    Widget { id: w }
    Component.onCompleted: {
        console.log("width:", w.width)
        console.log("title:", w.title)
    }
}
"""
        _load_qml(self.engine, tmp_path, qml, qtbot)
        print(self.captured)
        assert any("width: 100" in m for m in self.captured), self.captured
        assert any("title: default" in m for m in self.captured), self.captured

    def test_plain_attr_writable_from_qml(self, qtbot, tmp_path):
        """QML should be able to write to the auto-property."""

        class Counter:
            def __init__(self):
                self.count = 0

        bridge_type(Counter, uri="AutoPropWriteBackend", version="1.0")

        qml = """
import QtQuick 2.0
import AutoPropWriteBackend 1.0
Item {
    Counter { id: c }
    Component.onCompleted: {
        c.count = 5
        console.log("count:", c.count)
    }
}
"""
        _load_qml(self.engine, tmp_path, qml, qtbot)
        assert any("count: 5" in m for m in self.captured), self.captured


class TestExplicitPropertyNotOverridden:
    """Classes with hand-written @property descriptors must be left alone by
    the auto-property machinery and still work correctly via bridge_instance."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured = []
        qInstallMessageHandler(lambda t, c, m: self.captured.append(m))

    def teardown_method(self):
        del self.engine
        self.engine = None
        qInstallMessageHandler(None)
        self.captured.clear()

    def test_explicit_property_not_replaced(self, qtbot, tmp_path,
                                              capsys: pytest.CaptureFixture[str]):
        """A class with @property + custom setter must keep its own descriptor;
        the auto-property must not wrap over it."""

        class ManualPropModel:
            def __init__(self):
                self._value = 0

            @property
            def value(self):
                return self._value

            @value.setter
            def value(self, v):
                print(f"custom setter called with {v}")
                self._value = v

        obj = ManualPropModel()
        bridge_instance(obj, name="ManualPropModel")

        qml = """
import QtQuick 2.0
import backend 1.0
Item {
    Component.onCompleted: {
        ManualPropModel.value = 77
        console.log("value:", ManualPropModel.value)
    }
}
"""
        _load_qml(self.engine, tmp_path, qml, qtbot)

        captured = capsys.readouterr()
        assert "custom setter called with 77" in captured.out
        assert obj.value == 77

        # Ensure _value was not auto-wrapped (it starts with '_')
        assert not isinstance(type(obj).__dict__.get("_value"), property)

    def test_explicit_property_with_signal(self, qtbot, tmp_path,
                                            capsys: pytest.CaptureFixture[str]):
        """A class with a hand-written Signal + @property (CounterModel pattern)
        must work exactly as before"""

        class CounterModel:
            countChanged = Signal(int)

            def __init__(self):
                self._count = 0

            @property
            def count(self):
                return self._count

            @count.setter
            def count(self, value: int):
                if self._count != value:
                    print(f"count setter: {self._count} -> {value}")
                    self._count = value
                    self.countChanged.emit(self._count)

        obj = CounterModel()
        bridge_instance(obj, name="CounterModel")

        # _count must remain a plain int, not an auto-property
        assert not isinstance(type(obj).__dict__.get("_count"), property), (
            "_count must not be turned into an auto-property"
        )
        # count must be the original @property, not auto-replaced
        descriptor = type(obj).__dict__.get("count")
        assert isinstance(descriptor, property), (
            "count must remain the hand-written @property descriptor"
        )

        qml = """
import QtQuick 2.0
import backend 1.0
Item {
    property int signalFired: 0
    Component.onCompleted: {
        CounterModel.countChanged.connect(function(v) {
            signalFired++
            console.log("countChanged:", v)
        })
        CounterModel.count = 3
        CounterModel.count = 3   // duplicate — no signal
        CounterModel.count = 7
    }
}
"""
        root = _load_qml(self.engine, tmp_path, qml, qtbot)

        captured = capsys.readouterr()
        assert "count setter: 0 -> 3" in captured.out
        assert "count setter: 3 -> 7" in captured.out
        assert obj.count == 7

        # Signal fired for each distinct value change
        assert root.property("signalFired") == 2

class TestExplicitPropertyNotOverriddenBridgeType:
    """Same guarantees as above but for QML-creatable types (bridge_type)."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured = []
        qInstallMessageHandler(lambda t, c, m: self.captured.append(m))

    def teardown_method(self):
        del self.engine
        self.engine = None
        qInstallMessageHandler(None)
        self.captured.clear()

    def test_counter_model_pattern(self, qtbot, tmp_path,
                                    capsys: pytest.CaptureFixture[str]):
        """Replicate the counter example: bridge_type on a class that has
        self._count and @property count with a custom Signal. The auto-property
        machinery must not touch _count or replace the count @property."""

        class CounterTypeModel:
            countChanged = Signal(int)

            def __init__(self):
                self._count = 0

            @property
            def count(self):
                return self._count

            @count.setter
            def count(self, value: int):
                if self._count != value:
                    print(f"TypeCounter setter: {self._count} -> {value}")
                    self._count = value
                    self.countChanged.emit(self._count)

        bridge_type(CounterTypeModel, uri="CounterTypeBackend", version="1.0")

        # _count must not become a property
        assert not isinstance(type(CounterTypeModel).__dict__.get("_count"), property)
        # count must remain the hand-written @property
        assert isinstance(CounterTypeModel.__dict__.get("count"), property)

        qml = """
import QtQuick 2.0
import CounterTypeBackend 1.0
Item {
    CounterTypeModel { id: c }
    property int fired: 0
    Component.onCompleted: {
        c.countChanged.connect(function(v) { fired++ })
        c.count = 5
        c.count = 5   // duplicate
        c.count = 10
        console.log("final count:", c.count)
    }
}
"""
        root = _load_qml(self.engine, tmp_path, qml, qtbot)

        captured = capsys.readouterr()
        assert "TypeCounter setter: 0 -> 5" in captured.out
        assert "TypeCounter setter: 5 -> 10" in captured.out
        assert root.property("fired") == 2
        # qt logging
        assert any("final count: 10" in m for m in self.captured), self.captured

    def test_auto_props_disabled(self, qtbot, tmp_path):
        """Passing auto_properties=False must skip augmentation entirely."""

        class NoAutoWidget:
            def __init__(self):
                self.x = 0

        bridge_type(NoAutoWidget, uri="NoAutoBackend", version="1.0",
                    auto_properties=False)

        # x must not be a property descriptor on the class
        assert not isinstance(NoAutoWidget.__dict__.get("x"), property)
