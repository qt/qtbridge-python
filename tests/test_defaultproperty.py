# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

from typing import Optional
import pytest
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine
from QtBridge import bridge_type

class TestDefaultProperty:
    """Test default_property keyword with bridge_type"""

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

    def test_invalid_default_property(self):
        """Test that invalid default_property names are handled gracefully"""

        class InvalidBox:
            pass

        # This should not crash, but the default_property should be ignored
        # since the specified property doesn't exist
        bridge_type(InvalidBox, uri="test.defaultproperty.invalid", version="1.0", default_property="nonexistent")

        # Just verify the type was registered
        box = InvalidBox()
        assert box is not None

    def test_default_property_qml_assignment(self, qtbot):
        """Test default_property assignment works through QML"""

        # Minimal Widget and Box classes
        class Widget:
            def __init__(self):
                self._text = "Default"

            @property
            def text(self) -> str:
                return self._text

            @text.setter
            def text(self, value: str) -> None:
                self._text = value

        class Box:
            def __init__(self):
                self._child = None

            @property
            def child(self) -> Optional[Widget]:
                return self._child

            @child.setter
            def child(self, value) -> None:
                self._child = value

            def has_child(self) -> bool:
                return self._child is not None

        # Register types
        bridge_type(Widget, uri="test.defaultproperty.typed", version="1.0")
        bridge_type(Box, uri="test.defaultproperty.typed", version="1.0", default_property="child")

        # Test QML snippet that uses default property
        qml_content = """
import QtQuick 2.15
import test.defaultproperty.typed 1.0

Item {
    property Box testBox: Box {
        Widget {
            text: "Hello from Widget!"
        }
    }

    Component.onCompleted: {
        console.log("Box has child:", testBox.has_child())
        console.log("Widget text:", testBox.child ? testBox.child.text : "no child")
    }
}
"""

        # Install message handler to capture console output
        qInstallMessageHandler(self.message_handler)

        self.engine = QQmlApplicationEngine()
        self.engine.loadData(qml_content.encode(), QUrl())

        # Wait a bit for Component.onCompleted to execute
        qtbot.wait(100)

        # Verify the console output shows the default property assignment worked
        messages = self.get_console_messages()

        # Check that we got the expected console messages
        has_child_msg = any("Box has child: true" in msg for msg in messages)
        widget_text_msg = any("Widget text: Hello from Widget!" in msg for msg in messages)

        assert has_child_msg, f"Expected 'Box has child: true' message. Got: {messages}"
        assert widget_text_msg, f"Expected 'Widget text: Hello from Widget!' message. Got: {messages}"

    def test_default_property_correct_python_object_stored(self, qtbot, capsys):
        """Test that the correct Python backend object is stored when assigned via QML default property"""

        # Widget class with text property and a setter that prints to verify identity
        class Widget:
            def __init__(self):
                self._text = "Default"

            @property
            def text(self) -> str:
                return self._text

            @text.setter
            def text(self, value: str) -> None:
                self._text = value

        # Box class with a setter that prints the child's text to verify we get the Python object
        class Box:
            def __init__(self):
                self._child = None

            @property
            def child(self) -> Optional[Widget]:
                return self._child

            @child.setter
            def child(self, value) -> None:
                self._child = value
                # Print the text from the child to verify we have the actual Python backend object
                if value is not None:
                    print(f"Box.child setter received Widget with text: {value.text}")

            def get_child_text(self) -> str:
                return self._child.text if self._child else "no child"

        # Register types
        bridge_type(Widget, uri="test.defaultproperty.pythonobj", version="1.0")
        bridge_type(Box, uri="test.defaultproperty.pythonobj", version="1.0", default_property="child")

        # Test QML snippet that assigns a Widget to Box via default property
        qml_content = """
import QtQuick 2.15
import test.defaultproperty.pythonobj 1.0

Item {
    property Box testBox: Box {
        Widget {
            text: "Hello from Widget!"
        }
    }

    Component.onCompleted: {
        console.log("Child text from Python:", testBox.get_child_text())
    }
}
"""
        self.engine = QQmlApplicationEngine()
        self.engine.loadData(qml_content.encode(), QUrl())

        # Wait a bit for Component.onCompleted to execute
        qtbot.wait(100)

        # Capture stdout and verify the Python print statement
        captured = capsys.readouterr()

        # Check that the setter was called with the correct Python object
        # The print statement in the setter outputs to stdout
        assert "Box.child setter received Widget with text: Hello from Widget!" in captured.out, \
            f"Expected setter message with Widget text. Got stdout: {captured.out}"

    def test_default_property_qml_assignment_no_typehint(self, qtbot):
        """
        Test that QML shows 'Box has child: undefined' when has_child() has no return type hint.
        """
        class Widget:
            def __init__(self):
                self._text = "Hello from Widget!"

            @property
            def text(self):
                return self._text

            @text.setter
            def text(self, value):
                self._text = value

        class Box:
            def __init__(self):
                self._child = None

            @property
            def child(self):
                return self._child

            @child.setter
            def child(self, value):
                self._child = value

            def has_child(self):
                # No return type hint
                return self.child is not None

        bridge_type(Widget, uri="test.defaultproperty.notypehint", version="1.0")
        bridge_type(Box, uri="test.defaultproperty.notypehint", version="1.0", default_property="child")

        qml_content = """
import QtQuick 2.15
import test.defaultproperty.notypehint 1.0

Item {
    property Box testBox: Box {
        Widget {
            text: "Hello from Widget!"
        }
    }

    Component.onCompleted: {
        console.log("Box has child:", testBox.has_child())
        console.log("Widget text:", testBox.child ? testBox.child.text : "no child")
    }
}
"""

        # Setup message handler and engine
        self.captured_messages = []
        def handler(msg_type, context, message):
            self.captured_messages.append(message)
        qInstallMessageHandler(handler)
        self.engine = QQmlApplicationEngine()
        self.engine.loadData(bytes(qml_content, "utf-8"), QUrl())

        # Wait for QML to complete
        qtbot.wait(100)

        # Check for 'Box has child: undefined' in captured messages
        found = any("Box has child: undefined" in msg for msg in self.captured_messages)
        assert found, "QML did not show 'Box has child: undefined' when has_child() has no type hint"
