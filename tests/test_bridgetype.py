# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import os
import pytest
import tempfile
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_type, insert, remove, move, edit


class TestBridgeTypeDecorators:
    """Test that decorators (@insert, @remove, @move, @edit) work with bridge_type()"""

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
                    'backend instance' in msg['message'] or
                    'Bound decorator' in msg['message'] or
                    'does not have a data() method' in msg['message'])]
        if msg_type:
            messages = [msg for msg in messages if msg['type'] == msg_type]
        return messages

    def test_all_decorators_with_bridge_type(self, qtbot):
        """Test that all decorators (@insert, @remove, @move, @edit) work with bridge_type()"""
        self.setup_message_capture()

        class CompleteModel:
            def __init__(self):
                self._items = ["A", "B", "C"]

            @insert
            def add_item(self, value: str, index: int = -1) -> bool:
                """Add an item at the specified index"""
                if index == -1:
                    self._items.append(value)
                else:
                    self._items.insert(index, value)
                return True

            @remove
            def remove_item(self, index: int) -> bool:
                """Remove an item at the specified index"""
                if 0 <= index < len(self._items):
                    del self._items[index]
                    return True
                return False

            @move
            def move_item(self, from_index: int, to_index: int) -> bool:
                """Move an item from one index to another"""
                if 0 <= from_index < len(self._items) and 0 <= to_index < len(self._items):
                    item = self._items.pop(from_index)
                    self._items.insert(to_index, item)
                    return True
                return False

            @edit
            def edit_item(self, index: int, value: str) -> bool:
                """Edit an item at the specified index"""
                if 0 <= index < len(self._items):
                    self._items[index] = value
                    return True
                return False

            def data(self) -> list[str]:
                """Return the data for QML"""
                return self._items

            @property
            def items(self) -> list[str]:
                """Expose items as a property"""
                return self._items

        # Register the type with QtBridges
        bridge_type(CompleteModel, uri="TestBackend", version="1.0")

        # Create QML that tests all decorators
        qml_content = """
        import QtQuick 2.15
        import TestBackend 1.0

        Item {
            CompleteModel {
                id: model
            }

            Component.onCompleted: {
                console.log("=== Testing all decorators ===");
                console.log("Initial:", JSON.stringify(model.items));

                // Test @insert
                model.add_item("D", -1);
                console.log("After insert D:", JSON.stringify(model.items));

                // Test @edit
                model.edit_item(0, "A_EDITED");
                console.log("After edit index 0:", JSON.stringify(model.items));

                // Test @move
                model.move_item(0, 2);
                console.log("After move 0->2:", JSON.stringify(model.items));

                // Test @remove
                model.remove_item(1);
                console.log("After remove index 1:", JSON.stringify(model.items));

                console.log("=== All decorator tests completed ===");
            }
        }
        """

        # Write QML to temporary file and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            temp_qml_path = f.name

        try:
            # Load QML
            self.engine.load(QUrl.fromLocalFile(temp_qml_path))
            qtbot.wait(200)  # Give time for all operations to complete

            completion_messages = [
                msg for msg in self.captured_messages
                if 'All decorator tests completed' in msg['message']
            ]
            assert len(completion_messages) > 0, "Test didn't complete successfully"

            binding_messages = self.get_qtbridge_messages()

            bound_messages = [
                msg for msg in binding_messages
                if 'Bound decorator' in msg['message']
            ]

            assert len(bound_messages) >= 4, (
                f"Expected at least 4 decorator binding messages, got {len(bound_messages)}: "
                f"{[msg['message'] for msg in bound_messages]}"
            )

            decorator_errors = [
                msg for msg in self.captured_messages
                if 'decorator has no bound backend instance' in msg['message']
            ]
            assert len(decorator_errors) == 0, f"Got decorator errors: {decorator_errors}"

        finally:
            os.unlink(temp_qml_path)


    def test_bridge_type_as_view_model(self, qtbot):
        """Test that bridge_type() created types work correctly as QML ListView models"""
        self.setup_message_capture()

        class TaskViewModel:
            def __init__(self):
                self._tasks = ["Task 1", "Task 2", "Task 3"]

            def data(self) -> list[str]:
                """Return the task list for QML"""
                return self._tasks

            @insert
            def add_task(self, task_name: str):
                """Add a new task"""
                self._tasks.append(task_name)
                return True

            @remove
            def delete_task(self, index: int) -> bool:
                """Remove a task at index"""
                if 0 <= index < len(self._tasks):
                    del self._tasks[index]
                    return True
                return False

            def get_count(self) -> int:
                """Get the number of tasks"""
                return len(self._tasks)

        # Register the type with QtBridges
        bridge_type(TaskViewModel, uri="TestBackend", version="1.0")

        # Create QML that uses the model in a ListView
        qml_content = """
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        import TestBackend 1.0

        Item {
            width: 400
            height: 300

            TaskViewModel {
                id: taskModel
            }

            ListView {
                id: listView
                anchors.fill: parent
                model: taskModel

                delegate: Rectangle {
                    required property int index
                    required property string display

                    width: listView.width
                    height: 40
                    color: index % 2 === 0 ? "#f0f0f0" : "#ffffff"

                    Text {
                        anchors.centerIn: parent
                        text: display
                        color: "#000000"
                    }
                }
            }

            Component.onCompleted: {
                console.log("=== Testing bridge_type() as ListView model ===");
                console.log("Initial count:", taskModel.get_count());

                // Verify initial data is displayed (3 items)
                if (listView.count !== 3) {
                    console.error("Expected 3 items, got:", listView.count);
                }

                // Test adding a task
                taskModel.add_task("New Task 4");
                console.log("After add, count:", taskModel.get_count());

                // Verify item was added
                if (listView.count !== 4) {
                    console.error("Expected 4 items after add, got:", listView.count);
                }

                // Test removing a task
                taskModel.delete_task(0);
                console.log("After delete, count:", taskModel.get_count());

                // Verify item was removed
                if (listView.count !== 3) {
                    console.error("Expected 3 items after delete, got:", listView.count);
                }

                console.log("=== bridge_type() view model test completed ===");
            }
        }
        """


        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            temp_qml_path = f.name

        try:
            self.engine.load(QUrl.fromLocalFile(temp_qml_path))
            qtbot.wait(300)  # Give time for all operations to complete

            # Check that no count mismatch errors occurred in QML
            qml_errors = [
                msg for msg in self.captured_messages
                if 'error' in msg['message'].lower() and 'Expected' in msg['message']
            ]
            assert len(qml_errors) == 0, f"Got QML count errors: {qml_errors}"

            # Check for successful completion message
            completion_messages = [
                msg for msg in self.captured_messages
                if 'bridge_type() view model test completed' in msg['message']
            ]
            assert len(completion_messages) > 0, "View model test didn't complete successfully"

            # Check that decorators were successfully bound
            bound_messages = [
                msg for msg in self.captured_messages
                if 'Bound decorator' in msg['message']
            ]
            assert len(bound_messages) >= 2, (
                f"Expected at least 2 decorator bindings (insert, remove), got {len(bound_messages)}"
            )

            # Verify data type was inferred correctly
            datatype_messages = [
                msg for msg in self.captured_messages
                if 'Inferred data type' in msg['message'] and 'List' in msg['message']
            ]
            assert len(datatype_messages) > 0, (
                f"Data type not inferred. Messages: {[msg['message'] for msg in self.get_qtbridge_messages()]}"
            )

        finally:
            os.unlink(temp_qml_path)

    def test_bridge_type_as_model_without_data_method(self, qtbot):
        """Test that error is logged when bridge_type() type is used as model without data() method"""
        self.setup_message_capture()

        class InvalidViewModel:
            def __init__(self):
                self._items = ["Item 1", "Item 2"]

            @insert
            def add_item(self, value: str):
                self._items.append(value)
                return True

            def get_count(self) -> int:
                return len(self._items)

        # Register the type with a unique URI to avoid collision
        bridge_type(InvalidViewModel, uri="test.invalid.model", version="1.0")

        # Create QML that tries to use the model in a ListView
        qml_content = """
        import QtQuick 2.15
        import test.invalid.model 1.0

        Item {
            InvalidViewModel {
                id: invalidModel
            }

            ListView {
                id: listView
                anchors.fill: parent
                model: invalidModel  // This should trigger the error

                delegate: Text {
                    required property string display
                    text: display
                }
            }

            Component.onCompleted: {
                console.log("ListView count:", listView.count);
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            temp_qml_path = f.name

        try:
            # Note: The error cannot be caught with pytest.raises() because it occurs
            # inside Qt's rowCount() callback, which can't propagate Python exceptions
            self.engine.load(QUrl.fromLocalFile(temp_qml_path))
            qtbot.wait(200)

            # Verify the error was logged to Qt messages
            messages = self.get_qtbridge_messages()
            error_messages = [
                msg['message'] for msg in messages
                if 'does not have a data() method' in msg['message']
            ]

            assert len(error_messages) > 0, (
                "Error about missing data() method should be logged"
            )

            error_msg = error_messages[0]
            assert 'InvalidViewModel' in error_msg, (
                "Error should mention the type name"
            )
            assert 'does not have a data() method' in error_msg, (
                "Error should mention missing data() method"
            )
            assert 'bridge_type()' in error_msg, (
                "Error should mention bridge_type()"
            )
            assert 'def data(self)' in error_msg, (
                "Error should provide example of data() method"
            )
        finally:
            os.unlink(temp_qml_path)

    def test_bridge_type_basic(self):
        """Test basic bridge_type functionality"""
        # Define a simple test class
        class SimpleType:
            def data(self):
                return []

        # This should not raise an exception
        bridge_type(SimpleType)

    def test_bridge_type_with_parameters(self):
        """Test bridge_type with custom parameters"""
        class CustomType:
            def data(self):
                return []

        bridge_type(CustomType, uri="test.backend", version="2.1")

    def test_bridge_type_invalid_version(self):
        """Test bridge_type with invalid version format"""
        class VersionType:
            def data(self):
                return []

        with pytest.raises(ValueError, match="version must be in format 'major.minor'"):
            bridge_type(VersionType, version="invalid")

    def test_bridge_type_invalid_type(self):
        """Test bridge_type with non-type argument"""
        with pytest.raises(TypeError):
            bridge_type("not_a_type")


if __name__ == "__main__":
    pytest.main([__file__])
