# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from pathlib import Path
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, insert, remove, edit

import pytest
from dataclasses import dataclass

TEST_QML_METHOD = """
import QtQuick 2.0
import backend 1.0

Item {
    width: 640
    height: 480

    Component.onCompleted: {
        Test_model.add_string("Test String")
    }
}
"""

TEST_QML_PROPERTY = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        TestModel.value = 456
    }
}
"""

class AutoQmlBridgeTest:
    def __init__(self):
        self._strings = []

    def add_string(self, new_string: str) -> bool:
        print(f"add_string called with {new_string}")  # For test
        self._strings.append(new_string)
        return True

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        print(f"Setter called with {v}")  # For test
        self._value = v

    def data(self):
        return self._strings

class TestBridgeInstance:
    """Test bridge_instance() functionality with various scenarios"""

    def setup_method(self):
        """Setup that runs before each test method"""
        self.engine = QQmlApplicationEngine()
        self.test_model = AutoQmlBridgeTest()
        self.captured_messages = []

    def teardown_method(self):
        """Cleanup after each test method"""
        if self.engine:
            del self.engine
            self.engine = None
        qInstallMessageHandler(None)
        self.captured_messages.clear()

    def message_handler(self, msg_type, context, message):
        """Capture console messages from QML"""
        self.captured_messages.append(message)

    def get_console_messages(self):
        """Get all captured console messages"""
        return [msg for msg in self.captured_messages if not msg.startswith("qml:")]

    def test_method_registration(self, qtbot, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        """Test basic functionality"""
        bridge_instance(self.test_model, name="Test_model")

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        # Load QML
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))

        # Wait for QML to load
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        # Verify model was updated
        assert len(self.test_model._strings) == 1
        assert self.test_model._strings[0] == "Test String"

        captured = capsys.readouterr()
        assert "add_string called with Test String" in captured.out

    def test_no_data_method(self, qtbot):
        """Test that error is raised when data() method is missing"""
        original_data_method = AutoQmlBridgeTest.data
        # Remove it from the class
        del AutoQmlBridgeTest.data

        try:
            with pytest.raises(
                TypeError,
                match=r"The class wrapped with bridge_instance must have a data\(\) method"
            ):
                bridge_instance(self.test_model, name="TestModel")
        finally:
            # Restore the original data() method
            AutoQmlBridgeTest.data = original_data_method

    def test_property_registration(self, qtbot, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        engine = QQmlApplicationEngine()
        test_model = AutoQmlBridgeTest()
        bridge_instance(test_model, name="TestModel")

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_PROPERTY)
        engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        captured = capsys.readouterr()
        assert "Setter called with 456" in captured.out

    def test_bridge_instance_no_typehint_empty_list(self):
        class ModelNoTypeHint:
            def data(self):
                return []

        # Should not raise error (current bridge_instance behavior)
        try:
            bridge_instance(ModelNoTypeHint(), name="NoTypeHintModel")
        except Exception as e:
            assert False, f"bridge_instance raised error unexpectedly: {e}"

    def test_bridge_instance_list_of_dataclass(self):
        from dataclasses import dataclass

        @dataclass
        class Item:
            value: int

        class ModelDataclass:
            def data(self):
                return [Item(1), Item(2)]

        try:
            bridge_instance(ModelDataclass(), name="DataclassModel")
        except Exception as e:
            assert False, f"bridge_instance raised error for dataclass list: {e}"

    def test_bridge_instance_list_of_str(self):
        class ModelStrList:
            def data(self):
                return ["a", "b", "c"]

        try:
            bridge_instance(ModelStrList(), name="StrListModel")
        except Exception as e:
            assert False, f"bridge_instance raised error for str list: {e}"

    def test_bridge_instance_basic(self):
        """Test basic bridge_instance functionality"""
        class SimpleModel:
            def data(self):
                return []

        try:
            bridge_instance(SimpleModel(), name="SimpleModel")
        except Exception as e:
            assert False, f"bridge_instance raised error unexpectedly: {e}"

    def test_bridge_instance_with_custom_name(self, qtbot):
        """Test bridge_instance with custom name parameter"""
        class NamedModel:
            def __init__(self):
                self._items = ["Item1", "Item2"]

            def data(self):
                return self._items

        model = NamedModel()
        bridge_instance(model, name="CustomNamedModel")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("Model registered:", typeof CustomNamedModel !== 'undefined')
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(100)

        messages = self.get_console_messages()
        assert any("Model registered: true" in msg for msg in messages), \
            f"Expected model to be registered. Got: {messages}"

    def test_bridge_instance_default_backend_uri(self, qtbot):
        """Test that default uri 'backend' works"""
        class StringListModel:
            def __init__(self):
                self._strings: list[str] = ["Apple", "Banana", "Cherry"]

            def data(self) -> list[str]:
                return self._strings

            def get_count(self) -> int:
                return len(self._strings)

        model = StringListModel()
        bridge_instance(model, name="StringModel")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("Count:", StringModel.get_count())
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(100)

        messages = self.get_console_messages()
        assert any("Count: 3" in msg for msg in messages), \
            f"Expected 'Count: 3' message. Got: {messages}"

    def test_bridge_instance_custom_uri(self, qtbot):
        """Test that custom uri works correctly"""
        class CustomUriModel:
            def __init__(self):
                self._data: list[str] = ["Data1", "Data2", "Data3"]

            def data(self) -> list[str]:
                return self._data

            def get_count(self) -> int:
                return len(self._data)

        model = CustomUriModel()
        bridge_instance(model, name="CustomModel", uri="myapp.models")

        qml_content = """
import QtQuick 2.15
import myapp.models 1.0

Item {
    Component.onCompleted: {
        console.log("Custom URI Count:", CustomModel.get_count())
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(100)

        messages = self.get_console_messages()
        assert any("Custom URI Count: 3" in msg for msg in messages), \
            f"Expected 'Custom URI Count: 3' message. Got: {messages}"

    def test_bridge_instance_invalid_name(self):
        """Test bridge_instance with invalid name (must start with uppercase)"""
        class InvalidNameModel:
            def data(self):
                return []

        model = InvalidNameModel()

        qInstallMessageHandler(self.message_handler)

        # This should produce a Qt warning about invalid singleton type name
        bridge_instance(model, name="invalidName")

        messages = self.get_console_messages()
        assert any("Invalid QML singleton type name" in msg and "invalidName" in msg for msg in messages), \
            f"Expected warning about invalid name, got messages: {messages}"

    def test_bridge_instance_missing_name(self):
        """Test bridge_instance without name parameter"""
        class NoNameModel:
            def data(self):
                return []

        model = NoNameModel()

        # Should raise TypeError for missing required argument
        with pytest.raises(TypeError):
            bridge_instance(model)

    def test_bridge_instance_with_decorators(self, qtbot):
        """Test that decorators work with bridge_instance"""
        class DecoratorModel:
            def __init__(self):
                self._items = ["Original"]

            @insert
            def add_item(self, index: int, value: str):
                self._items.insert(index, value)

            @remove
            def remove_item(self, index: int):
                del self._items[index]

            @edit
            def edit_item(self, index: int, value: str):
                self._items[index] = value

            def data(self):
                return self._items

        model = DecoratorModel()
        bridge_instance(model, name="DecoratorModel")

        # Just verify the instance is created with decorators
        assert hasattr(model, 'add_item')
        assert hasattr(model, 'remove_item')
        assert hasattr(model, 'edit_item')

    def test_bridge_instance_with_properties(self, qtbot, tmp_path: Path):
        """Test bridge_instance with Python properties"""
        class PropertyModel:
            def __init__(self):
                self._items = []
                self._name = "TestModel"

            @property
            def name(self):
                return self._name

            @name.setter
            def name(self, value):
                print(f"Name changed to: {value}")
                self._name = value

            def data(self):
                return self._items

        model = PropertyModel()
        bridge_instance(model, name="PropModel")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    Component.onCompleted: {
        PropModel.name = "ChangedName"
    }
}
"""
        qml_file = tmp_path / "test_prop.qml"
        qml_file.write_text(qml_content)

        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            self.engine.load(QUrl.fromLocalFile(str(qml_file)))
            qtbot.wait(100)

            output = captured_output.getvalue()
            assert "Name changed to: ChangedName" in output
        finally:
            sys.stdout = old_stdout

    def test_bridge_instance_with_methods(self, qtbot, tmp_path: Path):
        """Test bridge_instance with callable methods"""
        class MethodModel:
            def __init__(self):
                self._counter = 0

            def increment(self):
                self._counter += 1
                print(f"Counter: {self._counter}")
                return self._counter

            def get_value(self):
                return self._counter

            def data(self):
                return [self._counter]

        model = MethodModel()
        bridge_instance(model, name="MethodModel")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    Component.onCompleted: {
        MethodModel.increment()
        MethodModel.increment()
    }
}
"""
        qml_file = tmp_path / "test_method.qml"
        qml_file.write_text(qml_content)

        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            self.engine.load(QUrl.fromLocalFile(str(qml_file)))
            qtbot.wait(100)

            output = captured_output.getvalue()
            assert "Counter: 1" in output
            assert "Counter: 2" in output
        finally:
            sys.stdout = old_stdout

    def test_bridge_instance_with_dataclass_list(self):
        """Test bridge_instance with list of dataclasses"""
        @dataclass
        class Person:
            name: str
            age: int

        class DataclassListModel:
            def __init__(self):
                self._people = [
                    Person("Alice", 30),
                    Person("Bob", 25)
                ]

            def data(self):
                return self._people

        model = DataclassListModel()
        try:
            bridge_instance(model, name="PeopleModel")
        except Exception as e:
            assert False, f"bridge_instance failed with dataclass list: {e}"

    def test_bridge_instance_with_int_list(self):
        """Test bridge_instance with list of integers"""
        class IntListModel:
            def data(self):
                return [1, 2, 3, 4, 5]

        model = IntListModel()
        try:
            bridge_instance(model, name="IntModel")
        except Exception as e:
            assert False, f"bridge_instance failed with int list: {e}"

    def test_bridge_instance_with_mixed_types(self):
        """Test bridge_instance with mixed type list"""
        class MixedListModel:
            def data(self):
                return [1, "two", 3.0, True]

        model = MixedListModel()
        try:
            bridge_instance(model, name="MixedModel")
        except Exception as e:
            assert False, f"bridge_instance failed with mixed type list: {e}"

    def test_bridge_instance_same_name_different_uri(self, qtbot):
        """Test that same name can be used with different URIs"""
        class ModelV1:
            def data(self) -> list[str]:
                return ["v1"]

            def get_version(self) -> str:
                return "1.0"

        class ModelV2:
            def data(self) -> list[str]:
                return ["v2"]
            def get_version(self) -> str:
                return "2.0"

        model1 = ModelV1()
        model2 = ModelV2()

        bridge_instance(model1, name="VersionModel", uri="app.v1")
        bridge_instance(model2, name="VersionModel", uri="app.v2")

        qml_content = """
import QtQuick 2.15
import app.v1 1.0 as V1
import app.v2 1.0 as V2

Item {
    Component.onCompleted: {
        console.log("V1:", V1.VersionModel.get_version())
        console.log("V2:", V2.VersionModel.get_version())
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(100)

        messages = self.get_console_messages()
        assert any("V1: 1.0" in msg for msg in messages), \
            f"Expected 'V1: 1.0'. Got: {messages}"
        assert any("V2: 2.0" in msg for msg in messages), \
            f"Expected 'V2: 2.0'. Got: {messages}"

    def test_bridge_instance_empty_data(self):
        """Test bridge_instance with empty data() return"""
        class EmptyModel:
            def data(self):
                return []

        model = EmptyModel()
        try:
            bridge_instance(model, name="EmptyModel")
        except Exception as e:
            assert False, f"bridge_instance failed with empty data: {e}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
