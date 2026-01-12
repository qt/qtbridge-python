# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

import os
import pytest
import tempfile
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, bridge_type, insert, remove, move, edit, reset, complete


class TestQAIMDecorators:
    """Test QAbstractItemModel decorators (@insert, @remove, @move, @edit) behavior"""

    def setup_method(self):
        """Setup that runs before each test method"""
        self.engine = QQmlApplicationEngine()
        self.captured_messages = []
        self.original_handler = None

    def teardown_method(self):
        """Cleanup after each test"""
        if self.original_handler:
            qInstallMessageHandler(self.original_handler)

    def message_handler(self, msg_type, context, message):
        """Custom Qt message handler to capture log messages"""
        self.captured_messages.append({
            'type': msg_type,
            'message': message,
            'context': context
        })

    def setup_message_capture(self):
        """Setup Qt message handler to capture log messages"""
        self.original_handler = qInstallMessageHandler(self.message_handler)

    def get_qtbridge_messages(self, msg_type=None):
        """Get captured QtBridge log messages, optionally filtered by type"""
        messages = [msg for msg in self.captured_messages if
                   ('qtbridges' in msg['message'].lower() or
                    '@remove' in msg['message'] or
                    '@insert' in msg['message'] or
                    '@move' in msg['message'] or
                    '@edit' in msg['message'] or
                    'qt_metacall' in msg['message'])]
        if msg_type:
            messages = [msg for msg in messages if msg['type'] == msg_type]
        return messages

    def test_insert_with_string_index_appends_gracefully(self, qtbot):
        """Test that passing a string index to @insert decorator"""
        self.setup_message_capture()

        class StringIndexModel:
            def __init__(self):
                self._items = ["A", "B"]

            @insert
            def add_item(self, value: str, index: str = "not_a_number"):
                self._items.append(value)
                return True

            @property
            def items(self):
                return self._items

            def data(self):
                return self._items

        model = StringIndexModel()
        bridge_instance(model, name="StringIndexModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0

        Item {
            Component.onCompleted: {
                StringIndexModel.add_item("C", "not_a_number")
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name

        try:
            with pytest.raises(TypeError, match="cannot be interpreted as an integer"):
                self.engine.load(QUrl.fromLocalFile(qml_path))
                qtbot.waitUntil(lambda: bool(self.engine.rootObjects()), timeout=2000)

            assert model.items == ["A", "B"], "No item should be appended if TypeError is raised"

        finally:
            os.unlink(qml_path)

    def test_insert_with_valid_numeric_index(self, qtbot):
        """Test that @insert works correctly with valid numeric index"""
        self.setup_message_capture()

        class NumericIndexModel:
            def __init__(self):
                self._items = ["First", "Last"]

            @insert
            def insert_item(self, value: str, index: int = -1):
                if index < 0 or index >= len(self._items):
                    self._items.append(value)
                else:
                    self._items.insert(index, value)
                return True

            def data(self):
                return self._items

        model = NumericIndexModel()
        bridge_instance(model, name="NumericIndexModel")

        # QML that calls insert_item with a valid numeric index
        qml_content = """
        import QtQuick 2.0
        import backend 1.0

        Item {
            Component.onCompleted: {
                NumericIndexModel.insert_item("Middle", 1)
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name

        try:
            self.engine.load(QUrl.fromLocalFile(qml_path))
            qtbot.waitUntil(lambda: bool(self.engine.rootObjects()), timeout=2000)

            # Should insert at the specified index
            expected = ["First", "Middle", "Last"]
            assert model.data() == expected

        finally:
            os.unlink(qml_path)

    def test_decorator_parameter_validation_basic(self, qtbot):
        """Test basic decorator parameter validation and graceful handling"""

        class ValidDecorators:
            def __init__(self):
                self._items = ["Item1", "Item2", "Item3"]

            @insert
            def add_item(self, value: str, index: int = -1):
                if index < 0:
                    self._items.append(value)
                else:
                    self._items.insert(index, value)
                return True

            @remove
            def remove_item(self, index: int):
                if 0 <= index < len(self._items):
                    self._items.pop(index)
                    return True
                return False

            @move
            def move_item(self, from_index: int, to_index: int):
                if (0 <= from_index < len(self._items) and
                    0 <= to_index < len(self._items)):
                    item = self._items.pop(from_index)
                    self._items.insert(to_index, item)
                    return True
                return False

            @edit
            def edit_item(self, index: int, value: str):
                if 0 <= index < len(self._items):
                    self._items[index] = value
                    return True
                return False

            def data(self):
                return self._items

        model = ValidDecorators()
        bridge_instance(model, name="ValidDecorators")

        # Test that all decorators can be registered without errors
        assert len(model.data()) == 3
        assert model.data()[0] == "Item1"


    def test_remove_with_valid_index(self, qtbot):
        """Test @remove called from QML with valid index removes item"""

        class RemoveModel:
            def __init__(self):
                self._items = ["A", "B"]
            @remove
            def remove_item(self, index: int):
                self._items.pop(index)
                return True
            def data(self):
                return self._items

        model = RemoveModel()
        bridge_instance(model, name="RemoveModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        Item { Component.onCompleted: { RemoveModel.remove_item(1) } }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            self.engine.load(QUrl.fromLocalFile(qml_path))
            qtbot.wait(100)
            assert model.data() == ["A"], "Item at index 1 should be removed"
        finally:
            os.unlink(qml_path)

    def test_remove_qml_invalid_index(self, qtbot):
        """Test @remove called from QML with string index fails gracefully and logs error"""

        class RemoveModel:
            def __init__(self):
                self._items = ["A", "B", "C"]

            @remove
            def remove_item(self, index: int):
                self._items.pop(index)
                return True

            def data(self):
                return self._items

        model = RemoveModel()
        bridge_instance(model, name="RemoveModelQML")

        # QML content that passes string value instead of integer
        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        Item {
            Component.onCompleted: {
                // This should fail - passing string instead of integer
                RemoveModelQML.remove_item("invalid_index")
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            # Install message handler after engine is created, just before QML load
            self.setup_message_capture()
            with pytest.raises(TypeError, match=r"'str' object cannot be interpreted as an integer"):
                self.engine.load(QUrl.fromLocalFile(qml_path))
                qtbot.wait(100)

            # Check that error was logged
            error_msgs = self.get_qtbridge_messages()
            found = any("@remove - Failed to convert" in msg['message'] or
                       "index argument to long" in msg['message'] for msg in error_msgs)
            assert found, "Expected error message for invalid string index from QML"

            # Model data should remain unchanged
            assert model.data() == ["A", "B", "C"], "Model should be unchanged when remove fails"
        finally:
            os.unlink(qml_path)

    def test_move_with_valid_indices(self, qtbot):
        """Test @move called from QML with valid indices moves item"""

        class MoveModel:
            def __init__(self):
                self._items = ["A", "B", "C"]

            @move
            def move_item(self, from_index: int, to_index: int):
                item = self._items.pop(from_index)
                self._items.insert(to_index, item)
                return True

            def data(self):
                return self._items

        model = MoveModel()
        bridge_instance(model, name="MoveModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        Item { Component.onCompleted: { MoveModel.move_item(0, 2) } }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            self.engine.load(QUrl.fromLocalFile(qml_path))
            qtbot.wait(100)
            assert model.data() == ["B", "C", "A"], "Item should be moved from 0 to 2"
        finally:
            os.unlink(qml_path)

    def test_move_qml_invalid_indices(self, qtbot):
        """Test @move called from QML with string indices fails gracefully and logs error"""
        class MoveModel:
            def __init__(self):
                self._items = ["A", "B", "C"]

            @move
            def move_item(self, from_index: int, to_index: int):
                item = self._items.pop(from_index)
                self._items.insert(to_index, item)
                return True

            def data(self):
                return self._items

        model = MoveModel()
        bridge_instance(model, name="MoveModelQML")

        # QML content that passes string values instead of integers
        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        Item {
            Component.onCompleted: {
                // This should fail - passing strings instead of integers
                MoveModelQML.move_item("invalid", "also_invalid")
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            # Install message handler to capture error logs
            self.setup_message_capture()
            with pytest.raises(TypeError, match=r"'str' object cannot be interpreted as an integer"):
                self.engine.load(QUrl.fromLocalFile(qml_path))
                qtbot.wait(100)

            # Check that error was logged
            error_msgs = self.get_qtbridge_messages()
            found = any("@move" in msg['message'] and "Failed to convert" in msg['message'] for msg in error_msgs)
            assert found, "Expected error message for invalid string indices from QML"

            # Model data should remain unchanged
            assert model.data() == ["A", "B", "C"], "Model should be unchanged when move fails"
        finally:
            os.unlink(qml_path)

    def test_edit_with_valid_arguments(self, qtbot):
        """Test @edit called from QML with valid arguments edits item"""
        class EditModel:
            def __init__(self):
                self._items = ["A", "B"]

            @edit
            def edit_item(self, index: int, value: str):
                self._items[index] = value
                return True

            def data(self):
                return self._items

        model = EditModel()
        bridge_instance(model, name="EditModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        Item { Component.onCompleted: { EditModel.edit_item(1, "X") } }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            self.engine.load(QUrl.fromLocalFile(qml_path))
            qtbot.wait(100)
            assert model.data() == ["A", "X"], "Item at index 1 should be edited to 'X'"
        finally:
            os.unlink(qml_path)

    def test_edit_python_missing_arguments(self, qtbot):
        """Test @edit called directly from Python with missing arguments raises TypeError and logs expected message"""
        class EditModel:
            def __init__(self):
                self._items = ["A", "B"]

            @edit
            def edit_item(self, index: int, value: str):
                self._items[index] = value
                return True

            def data(self):
                return self._items

        model = EditModel()
        bridge_instance(model, name="EditModelPy")

        # Missing value argument
        with pytest.raises(ValueError):
            model.edit_item(0)

        assert model.data() == ["A", "B"], "No item should be edited if argument is missing"

    def test_edit_python_invalid_index(self, qtbot):
        """Test @edit called directly from Python with invalid index raises TypeError and logs expected message"""

        class EditModel:
            def __init__(self):
                self._items = ["A", "B"]

            @edit
            def edit_item(self, index: int, value: str):
                self._items[index] = value
                return True

            def data(self):
                return self._items

        model = EditModel()
        bridge_instance(model, name="EditModelPy")

        # Invalid index argument (string instead of int)
        with pytest.raises(TypeError):
            model.edit_item("not_an_int", "X")

    def test_reset_qml(self, qtbot):
        """Test @reset called from QML resets all data in the model correctly"""

        class ResetModel:
            def __init__(self):
                self._items = ["A", "B", "C"]

            @reset
            def reset_model(self):
                self._items = ["X", "Y"]
                return True

            def data(self):
                return self._items

        model = ResetModel()
        bridge_instance(model, name="ResetModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        Item { Component.onCompleted: { ResetModel.reset_model() } }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            self.engine.load(QUrl.fromLocalFile(qml_path))
            qtbot.wait(100)
            assert model.data() == ["X", "Y"], "Model should be reset with new data"
        finally:
            os.unlink(qml_path)

    def test_reset_python(self, qtbot):
        """Test @reset called directly from Python resets the model correctly"""

        class ResetModel:
            def __init__(self):
                self._items = ["A", "B", "C", "D"]

            @reset
            def clear_all(self):
                self._items = []
                return True

            def data(self):
                return self._items

        model = ResetModel()
        bridge_instance(model, name="ResetModelPy")

        result = model.clear_all()
        assert result is True, "Reset method should return True"
        assert model.data() == [], "Model should be empty after reset"

    def test_reset_with_bridge_type(self, qtbot):
        """Test @reset works correctly with bridge_type registration"""

        class ResetTypeModel:
            def __init__(self):
                self._items = ["A", "B", "C"]

            @reset
            def reset_data(self):
                self._items = ["Reset"]
                return True

            def data(self):
                return self._items

        bridge_type(ResetTypeModel, name="ResetTypeModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0
        ResetTypeModel {
            id: model
            Component.onCompleted: { model.reset_data() }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name
        try:
            self.engine.load(QUrl.fromLocalFile(qml_path))
            qtbot.wait(100)
            # Note: We can't directly check the model data in this case
            # since we don't have a direct reference to the QML-created instance
        finally:
            os.unlink(qml_path)

    def test_reset_error_handling(self, qtbot):
        """Test @reset handles exceptions in the decorated method properly"""

        class ResetModel:
            def __init__(self):
                self._items = ["A", "B"]

            @reset
            def failing_reset(self):
                raise ValueError("Reset failed!")

            def data(self):
                return self._items

        model = ResetModel()
        bridge_instance(model, name="ResetModelError")

        # Should raise the original exception
        with pytest.raises(ValueError, match="Reset failed!"):
            model.failing_reset()

        # Model should remain unchanged after failed reset
        assert model.data() == ["A", "B"], "Model should be unchanged after failed reset"

    def test_reset_with_return_value(self, qtbot):
        """Test @reset preserves return values from the decorated method"""

        class ResetModel:
            def __init__(self):
                self._items = ["A", "B"]

            @reset
            def reset_with_value(self):
                self._items = ["New"]
                return "Success"

            @reset
            def reset_no_return(self):
                self._items = ["Empty"]
                # No explicit return (should return None)

            def data(self):
                return self._items

        model = ResetModel()
        bridge_instance(model, name="ResetModelReturn")

        result1 = model.reset_with_value()
        assert result1 == "Success", "Should return the method's return value"
        assert model.data() == ["New"], "Model should be reset"

        result2 = model.reset_no_return()
        assert result2 is None, "Should return None when method has no explicit return"
        assert model.data() == ["Empty"], "Model should be reset again"

    def test_complete_decorator_with_bridge_type(self, qtbot, capsys):
        """Test that @complete decorator is called when QML component is complete"""
        self.setup_message_capture()

        class InitializableComponent:
            def __init__(self):
                self._initialized = False
                self._init_count = 0

            @property
            def initialized(self) -> bool:
                return self._initialized

            @initialized.setter
            def initialized(self, value: bool) -> None:
                self._initialized = value

            @property
            def initCount(self) -> int:
                return self._init_count

            @complete
            def componentComplete(self) -> None:
                """This should be called automatically when QML component is complete"""
                print(
                    f"@complete: componentComplete called, count before: {self._init_count}",
                    flush=True
                )
                self._initialized = True
                self._init_count += 1
                print(
                    f"@complete: componentComplete finished, initialized={self._initialized}, "
                    f"count={self._init_count}",
                    flush=True
                )

            def getData(self) -> str:
                """Return initialization status"""
                return f"Initialized: {self._initialized}, Count: {self._init_count}"

        # Register the type with bridge_type - use unique URI to avoid conflicts with other tests
        bridge_type(InitializableComponent, uri="test.complete.basic", version="1.0")

        # Create QML that instantiates the component
        qml_content = """
        import QtQuick 2.15
        import test.complete.basic 1.0

        InitializableComponent {
            id: component

            Component.onCompleted: {
                console.log("QML Component.onCompleted - initialized:", component.initialized);
                console.log("QML Component.onCompleted - initCount:", component.initCount);
                console.log("QML Component.onCompleted - getData:", component.getData());
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            temp_qml_path = f.name

        try:
            self.engine.load(QUrl.fromLocalFile(temp_qml_path))
            qtbot.wait(200)  # Give time for component completion

            # Capture stdout to check Python print statements
            captured = capsys.readouterr()

            # Check that @complete method was called via print output
            assert '@complete: componentComplete called' in captured.out, (
                f"Expected @complete method to be called. Captured output: {captured.out}"
            )
            assert '@complete: componentComplete finished' in captured.out, (
                f"Expected @complete method to finish. Captured output: {captured.out}"
            )

            # Verify initialization happened via QML console output
            qml_messages = [
                msg for msg in self.captured_messages
                if 'QML Component.onCompleted' in msg['message']
            ]
            assert len(qml_messages) >= 3, (
                f"Expected at least 3 QML completion messages, got {len(qml_messages)}"
            )

            # Check that initialized property was set to true
            initialized_true_msgs = [
                msg for msg in self.captured_messages
                if 'initialized: true' in msg['message'].lower()
            ]
            assert len(initialized_true_msgs) > 0, (
                "Expected to see 'initialized: true' in QML output"
            )

        finally:
            os.unlink(temp_qml_path)

    def test_complete_decorator_with_property_updates(self, qtbot, capsys):
        """Test that property changes in @complete methods trigger UI updates"""
        self.setup_message_capture()

        class ServiceComponent:
            def __init__(self):
                self._ready = False
                self._status = "Not initialized"

            @property
            def ready(self) -> bool:
                return self._ready

            @ready.setter
            def ready(self, value: bool) -> None:
                self._ready = value

            @property
            def status(self) -> str:
                return self._status

            @status.setter
            def status(self, value: str) -> None:
                self._status = value

            @complete
            def initialize(self) -> None:
                """Initialize the service on component complete"""
                print("@complete: Initializing service", flush=True)
                self.ready = True
                self.status = "Initialized and ready"
                print(
                    f"@complete: Service initialized, ready={self._ready}, status={self._status}",
                    flush=True
                )

            def getInfo(self) -> str:
                return f"Ready: {self._ready}, Status: {self._status}"

        bridge_type(ServiceComponent, uri="test.complete.properties", version="1.0")

        qml_content = """
        import QtQuick 2.15
        import test.complete.properties 1.0

        ServiceComponent {
            id: service

            Component.onCompleted: {
                console.log("Service ready:", service.ready);
                console.log("Service status:", service.status);
                console.log("Service info:", service.getInfo());
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            temp_qml_path = f.name

        try:
            self.engine.load(QUrl.fromLocalFile(temp_qml_path))
            qtbot.wait(200)

            # Capture stdout to check Python print statements
            captured = capsys.readouterr()

            # Verify @complete was called via stdout
            assert '@complete: Initializing service' in captured.out, (
                f"Expected @complete initialization message. Captured output: {captured.out}"
            )
            assert '@complete: Service initialized' in captured.out, (
                f"Expected @complete completion message. Captured output: {captured.out}"
            )

            # Verify properties were updated via QML console output
            ready_true_msgs = [
                msg for msg in self.captured_messages
                if 'ready: true' in msg['message'].lower()
            ]
            assert len(ready_true_msgs) > 0, "Expected to see 'ready: true' in QML output"

            # Verify status was updated via QML console output
            status_msgs = [
                msg for msg in self.captured_messages
                if 'Initialized and ready' in msg['message']
            ]
            assert len(status_msgs) > 0, "Expected to see updated status in QML output"

        finally:
            os.unlink(temp_qml_path)

