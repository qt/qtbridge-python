# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import sys
import pytest
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, bridge_type, reset

class UserModel:
    def __init__(self):
        self._users = ["Alice", "Bob", "Charlie"]

    def data(self):
        return self._users

    @reset
    def set_users(self, users):
        self._users = users

class TestMethodReturn:
    """Test that methods and properties returning registered bridge_instance types
    are transparently converted to AutoQmlBridgeModel for QML"""

    def setup_method(self):
        """Setup for each test method"""
        self.captured_messages = []

    def teardown_method(self):
        """Cleanup after each test"""
        qInstallMessageHandler(None)
        self.captured_messages.clear()

    def message_handler(self, msg_type, context, message):
        """Capture console messages from QML"""
        self.captured_messages.append(message)

    def setup_message_capture(self):
        """Setup message handler to capture QML console output"""
        qInstallMessageHandler(self.message_handler)

    def get_console_messages(self):
        """Get all captured console messages"""
        return [msg for msg in self.captured_messages if not msg.startswith("qml:")]

    def test_property_returns_model(self, qtbot):
        """Test that properties returning registered Python objects work in QML"""
        class UserResource:
            def __init__(self):
                self._model = UserModel()
                bridge_instance(self._model, name="UserModel")

            @property
            def model(self):
                return self._model


        bridge_type(UserResource, uri="test.methodreturn.property", version="1.0")

        # QML that uses userResource.model in a ListView
        qml = """
import QtQuick 2.15
import test.methodreturn.property 1.0

Item {
    id: root
    width: 300; height: 200
    UserResource {
        id: userResource
    }

    ListView {
        id: userListView
        anchors.fill: parent
        model: userResource.model
        delegate: Text {
            text: modelData
        }
    }

    Component.onCompleted: {
        // Check model count and first/last items via ListView
        console.log("ListView count:", userListView.count);
    }
}
"""

        self.setup_message_capture()
        engine = QQmlApplicationEngine()
        engine.loadData(qml.encode('utf-8'), QUrl())

        # Wait for QML to load
        qtbot.waitUntil(lambda: len(self.get_console_messages()) >= 3, timeout=3000)

        messages = self.get_console_messages()
        assert any("ListView count: 3" in msg for msg in messages), \
            f"Expected ListView count message, got: {messages}"

    def test_method_returns_model(self, qtbot):
        """Test that a public method returning a registered model works in QML ListView"""
        class UserResource:
            def __init__(self):
                self._model = UserModel()
                # Register the model so it can be converted
                bridge_instance(self._model, name="UserModel")

            def model(self) -> UserModel:
                """Method that returns a registered model instance"""
                return self._model

        bridge_type(UserResource, uri="test.methodreturn.method", version="1.0")

        qml = """
import QtQuick 2.15
import test.methodreturn.method 1.0

Item {
    id: root
    width: 300; height: 200
    UserResource {
        id: userResource
    }

    ListView {
        id: userListView
        anchors.fill: parent
        model: userResource.model()
        delegate: Text {
            text: modelData
        }
    }

    Component.onCompleted: {
        // Only check ListView count
        console.log("ListView count:", userListView.count);
    }
}
"""

        self.setup_message_capture()
        engine = QQmlApplicationEngine()
        engine.loadData(qml.encode('utf-8'), QUrl())

        # Wait for QML to load
        qtbot.waitUntil(lambda: len(self.get_console_messages()) >= 3, timeout=3000)

        messages = self.get_console_messages()
        assert any("ListView count: 3" in msg for msg in messages), \
            f"Expected ListView count message, got: {messages}"



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
