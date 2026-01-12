# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

import pytest
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine
from QtBridge import bridge_type
from typing import List, Any

class TestNestedTypesList:
    """Test PyQmlListProperty with nested types through default_property"""

    def setup_method(self):
        """Setup for each test method"""
        self.captured_messages = []
        self.engine = None

    def teardown_method(self):
        """Cleanup after each test method"""
        if self.engine:
            del self.engine
            self.engine = None
        qInstallMessageHandler(None)

    def message_handler(self, msg_type, context, message):
        """Capture console messages from QML"""
        self.captured_messages.append(message)

    def get_console_messages(self):
        """Get all captured console messages"""
        return [msg for msg in self.captured_messages if not msg.startswith("qml:")]

    def test_nested_widgets_qml_assignment(self, qtbot):
        """Test PyQmlListProperty with nested widgets through QML.
           If this works, it shows that atFunction() and appendFunction() are working correctly."""

        # Minimal Widget and Box classes with type hints

        class Widget:
            def __init__(self) -> None:
                self._text: str = "Default"

            @property
            def text(self) -> str:
                return self._text

            @text.setter
            def text(self, value: str) -> None:
                self._text = value

        class Box:
            def __init__(self) -> None:
                self._children: List[Widget] = []

            @property
            def children(self) -> List[Widget]:
                return self._children

            @children.setter
            def children(self, value: Any) -> None:
                if isinstance(value, list):
                    self._children = value
                else:
                    self._children.append(value)

            def count(self) -> int:
                return len(self._children)

            def has_children(self) -> bool:
                return len(self._children) > 0

        # Register types
        bridge_type(Widget, uri="test.nested.widgets", version="1.0")
        bridge_type(Box, uri="test.nested.widgets", version="1.0", default_property="children")

        # Test QML snippet with nested widgets
        qml_content = """
import QtQuick 2.15
import test.nested.widgets 1.0

Item {
    property Box testBox: Box {
        Widget { text: "A" }
        Widget { text: "B" }
        Widget { text: "C" }
    }

    Component.onCompleted: {
        console.log("=== PyQmlListProperty Nested Test ===")
        console.log("Box children count:", testBox.count())
        console.log("Box has children:", testBox.has_children())

        // Test accessing children through array indexing (PyQmlListProperty at() function)
        if (testBox.children.length >= 3) {
            console.log("First child text:", testBox.children[0] ? testBox.children[0].text : "null")
            console.log("Second child text:", testBox.children[1] ? testBox.children[1].text : "null")
            console.log("Third child text:", testBox.children[2] ? testBox.children[2].text : "null")
        }

        // Test children.length property (PyQmlListProperty countFunction)
        console.log("Children length:", testBox.children.length)

        console.log("=== Test Complete ===")
    }
}
"""

        # Install message handler to capture console output
        qInstallMessageHandler(self.message_handler)

        engine = QQmlApplicationEngine()
        engine.loadData(qml_content.encode(), QUrl())

        # Wait a bit for Component.onCompleted to execute
        qtbot.wait(100)

        # Verify the console output shows the PyQmlListProperty functionality worked
        messages = self.get_console_messages()

        # Check that we got the expected console messages for nested list functionality
        test_start_msg = any("PyQmlListProperty Nested Test" in msg for msg in messages)
        children_count_msg = any("Box children count: 3" in msg for msg in messages)
        has_children_msg = any("Box has children: true" in msg for msg in messages)
        first_child_msg = any("First child text: A" in msg for msg in messages)
        second_child_msg = any("Second child text: B" in msg for msg in messages)
        third_child_msg = any("Third child text: C" in msg for msg in messages)
        children_length_msg = any("Children length: 3" in msg for msg in messages)
        test_complete_msg = any("Test Complete" in msg for msg in messages)

        assert test_start_msg, f"Expected test start message. Got: {messages}"
        assert children_count_msg, f"Expected 'Box children count: 3' message. Got: {messages}"
        assert has_children_msg, f"Expected 'Box has children: true' message. Got: {messages}"
        assert first_child_msg, f"Expected 'First child text: A' message. Got: {messages}"
        assert second_child_msg, f"Expected 'Second child text: B' message. Got: {messages}"
        assert third_child_msg, f"Expected 'Third child text: C' message. Got: {messages}"
        assert children_length_msg, f"Expected 'Children length: 3' message. Got: {messages}"
        assert test_complete_msg, f"Expected test complete message. Got: {messages}"

    def test_clear_and_count_functions_with_signals(self, qtbot):
        """Test PyQmlListProperty clearFunction() and countFunction() with property change signals"""

        class Widget:
            def __init__(self) -> None:
                self._text: str = "Default"

            @property
            def text(self) -> str:
                return self._text

            @text.setter
            def text(self, value: str) -> None:
                self._text = value

        class Box:
            def __init__(self) -> None:
                self._children: List[Widget] = []

            @property
            def children(self) -> List[Widget]:
                return self._children

            @children.setter
            def children(self, value: Any) -> None:
                if isinstance(value, list):
                    self._children = value
                else:
                    self._children.append(value)

            def count(self) -> int:
                return len(self._children)

            def has_children(self) -> bool:
                return len(self._children) > 0

        # Register types
        bridge_type(Widget, uri="test.nested.clear", version="1.0")
        bridge_type(Box, uri="test.nested.clear", version="1.0", default_property="children")

        # Test QML snippet that tests clear function and count with signals
        qml_content = """
import QtQuick 2.15
import test.nested.clear 1.0

Item {
    property Box testBox: Box {
        Widget { text: "Widget1" }
        Widget { text: "Widget2" }
        Widget { text: "Widget3" }
    }

    property int changeSignalCount: 0

    // Connect to children property change signal
    Connections {
        target: testBox
        function onChildrenChanged() {
            changeSignalCount++
            console.log("Children changed signal received, count:", changeSignalCount)
        }
    }

    Component.onCompleted: {
        console.log("=== Clear and Count Function Test ===")

        // Test initial count via countFunction (testBox.children.length)
        console.log("Initial children count:", testBox.children.length)
        console.log("Initial Python count():", testBox.count())

        // Clear the children array (should trigger clearFunction)
        console.log("Clearing children array...")
        testBox.children = []

        // Test count after clear
        console.log("After clear - children count:", testBox.children.length)
        console.log("After clear - Python count():", testBox.count())
        console.log("After clear - has children:", testBox.has_children())

        // Add some children back to test append
        console.log("Adding children back...")
        testBox.children = [
            Qt.createQmlObject('import test.nested.clear 1.0; Widget { text: "New1" }', testBox, "widget1"),
            Qt.createQmlObject('import test.nested.clear 1.0; Widget { text: "New2" }', testBox, "widget2")
        ]

        // Test count after adding back
        console.log("After re-adding - children count:", testBox.children.length)
        console.log("After re-adding - Python count():", testBox.count())

        // Test accessing the new children
        if (testBox.children.length >= 2) {
            console.log("New first child text:", testBox.children[0] ? testBox.children[0].text : "null")
            console.log("New second child text:", testBox.children[1] ? testBox.children[1].text : "null")
        }

        console.log("Final change signal count:", changeSignalCount)
        console.log("=== Clear and Count Test Complete ===")
    }
}
"""

        # Install message handler to capture console output
        qInstallMessageHandler(self.message_handler)

        self.engine = QQmlApplicationEngine()
        self.engine.loadData(qml_content.encode(), QUrl())

        # Wait a bit for Component.onCompleted to execute
        qtbot.wait(200)  # Longer wait for Qt.createQmlObject operations

        # Verify the console output shows the clear and count functionality worked
        messages = self.get_console_messages()

        # Check that we got the expected console messages
        test_start_msg = any("Clear and Count Function Test" in msg for msg in messages)
        initial_count_msg = any("Initial children count: 3" in msg for msg in messages)
        initial_python_count_msg = any("Initial Python count(): 3" in msg for msg in messages)

        clearing_msg = any("Clearing children array" in msg for msg in messages)
        after_clear_count_msg = any("After clear - children count: 0" in msg for msg in messages)
        after_clear_python_count_msg = any("After clear - Python count(): 0" in msg for msg in messages)
        after_clear_has_children_msg = any("After clear - has children: false" in msg for msg in messages)

        adding_back_msg = any("Adding children back" in msg for msg in messages)
        after_readd_count_msg = any("After re-adding - children count: 2" in msg for msg in messages)
        after_readd_python_count_msg = any("After re-adding - Python count(): 2" in msg for msg in messages)

        new_first_child_msg = any("New first child text: New1" in msg for msg in messages)
        new_second_child_msg = any("New second child text: New2" in msg for msg in messages)

        # Check that property change signals were triggered
        change_signal_msg = any("Children changed signal received" in msg for msg in messages)
        test_complete_msg = any("Clear and Count Test Complete" in msg for msg in messages)

        assert test_start_msg, f"Expected test start message. Got: {messages}"
        assert initial_count_msg, f"Expected 'Initial children count: 3' message. Got: {messages}"
        assert initial_python_count_msg, f"Expected 'Initial Python count(): 3' message. Got: {messages}"

        assert clearing_msg, f"Expected 'Clearing children array' message. Got: {messages}"
        assert after_clear_count_msg, f"Expected 'After clear - children count: 0' message. Got: {messages}"
        assert after_clear_python_count_msg, f"Expected 'After clear - Python count(): 0' message. Got: {messages}"
        assert after_clear_has_children_msg, f"Expected 'After clear - has children: false' message. Got: {messages}"

        assert adding_back_msg, f"Expected 'Adding children back' message. Got: {messages}"
        assert after_readd_count_msg, f"Expected 'After re-adding - children count: 2' message. Got: {messages}"
        assert after_readd_python_count_msg, f"Expected 'After re-adding - Python count(): 2' message. Got: {messages}"

        assert new_first_child_msg, f"Expected 'New first child text: New1' message. Got: {messages}"
        assert new_second_child_msg, f"Expected 'New second child text: New2' message. Got: {messages}"

        assert change_signal_msg, f"Expected property change signal messages. Got: {messages}"
        assert test_complete_msg, f"Expected test complete message. Got: {messages}"
