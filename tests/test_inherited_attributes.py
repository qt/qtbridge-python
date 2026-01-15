# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import pytest
import tempfile
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine
from QtBridge import bridge_type

class BaseResource:
    def __init__(self) -> None:
        self._value: str = "base-value"

    @property
    def value(self) -> str:
        return self._value

    def base_method(self) -> str:
        return "called-from-qml"

class DerivedResource(BaseResource):
    pass

QML = """
import QtQuick 2.15
import test.inherited 1.0

Item {
    property DerivedResource testObj: DerivedResource {}

    Component.onCompleted: {
        console.log("Base method:", testObj.base_method());
        console.log("Base property:", testObj.value);
    }
}
"""

class TestInheritedAttributes:
    def setup_method(self):
        """Setup that runs before each test method"""
        self.engine = QQmlApplicationEngine()
        self.captured_messages = []
        self.original_handler = None

    def teardown_method(self):
        """Cleanup after each test"""
        if self.engine:
            del self.engine
            self.engine = None
        if self.original_handler:
            qInstallMessageHandler(self.original_handler)

    def message_handler(self, msg_type, context, message):
        """Custom Qt message handler to capture log messages"""
        self.captured_messages.append({
            'type': msg_type,
            'category': context.category if hasattr(context, 'category') else '',
            'message': message
        })

    def setup_message_capture(self):
        """Setup message capture for Qt logging"""
        self.captured_messages.clear()
        self.original_handler = qInstallMessageHandler(self.message_handler)

    def test_inherited_method_and_property_qml(self, qtbot):
        bridge_type(DerivedResource, uri="test.inherited", version="1.0")
        self.setup_message_capture()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(QML)
            qml_path = f.name

        self.engine.load(QUrl.fromLocalFile(qml_path))
        qtbot.wait(100)

        found_method = any("Base method: called-from-qml" in m['message'] for m in self.captured_messages)
        found_property = any("Base property: base-value" in m['message'] for m in self.captured_messages)
        assert found_method, "QML could not call base_method() of base class"
        assert found_property, "QML could not access value property of base class"
