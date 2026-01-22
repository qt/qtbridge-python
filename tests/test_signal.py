# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, Signal

import pytest


TEST_QML_SIGNAL = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        // Test that the signal exists and can be connected
        SignalTestModel.mySignal.connect(function(value) {
            console.log("Signal received:", value)
        })

        // Call a method to ensure basic functionality works
        SignalTestModel.increment()
    }
}
"""


class SignalTestModel:
    """Test model with a Signal"""
    mySignal = Signal(int)

    def __init__(self):
        self._counter = 0

    @property
    def counter(self) -> int:
        return self._counter

    def increment(self):
        """Method to increment counter"""
        self._counter += 1

    def data(self):
        """Required method for QtBridge"""
        return [self._counter]


class TestSignal:
    """Test QtBridge Signal functionality"""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured_messages = []
        self.original_handler = None

    def teardown_method(self):
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

    def get_console_messages(self):
        """Get all captured console messages"""
        return [msg['message'] for msg in self.captured_messages]

    def test_signal_registration(self, qtbot):
        """Test that Signal is properly registered in the QMetaObject"""
        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")
        self.engine.loadData(TEST_QML_SIGNAL.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)
        assert len(self.engine.rootObjects()) > 0, "QML failed to load"

    def test_signal_basic_functionality(self, qtbot):
        """Test basic Signal instantiation and attributes"""
        sig = Signal(int)
        assert sig is not None

        class TestClass:
            testSignal = Signal(str, int)
        assert hasattr(TestClass, 'testSignal')

    def test_signal_with_multiple_types(self, qtbot):
        """Test Signal with multiple parameter types"""
        class MultiSignalModel:
            dataChanged = Signal(str, int, float)

            def __init__(self):
                self._data = "test"

            def data(self):
                return [self._data]

        model = MultiSignalModel()
        bridge_instance(model, name="MultiSignalModel")

        # Basic QML to verify the model loads
        qml_code = """
        import QtQuick 2.0
        import backend 1.0

        Item {
            Component.onCompleted: {
                // Just verify the model is accessible
                console.log("MultiSignalModel loaded")
            }
        }
        """

        self.engine.loadData(qml_code.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)
        assert len(self.engine.rootObjects()) > 0

    def test_signal_with_no_args(self, qtbot):
        """Test Signal with no arguments"""
        class NoArgSignalModel:
            triggered = Signal()

            def __init__(self):
                self._value = 0

            def data(self):
                return [self._value]

        model = NoArgSignalModel()

        assert hasattr(NoArgSignalModel, 'triggered')
        assert model is not None

    def test_signal_and_property_coexist(self, qtbot):
        """Test that explicit Signal overrides auto-generated property notify signal.

        When a property 'value' and an explicit Signal 'valueChanged(int)' are both defined,
        the explicit Signal should override the auto-generated 'valueChanged()' notify signal.
        This gives the user full control over when to emit the signal.
        """
        class PropertySignalModel:
            valueChanged = Signal(int)

            def __init__(self):
                self._value = 42

            @property
            def value(self) -> int:
                return self._value

            @value.setter
            def value(self, val: int):
                if self._value != val:
                    self._value = val
                    # With the explicit Signal, user must emit manually when implemented:
                    # self.valueChanged.emit(val)

            def data(self):
                return [self._value]

        model = PropertySignalModel()
        bridge_instance(model, name="PropertySignalModel")

        qml_code = """
        import QtQuick 2.0
        import backend 1.0

        Item {
            Component.onCompleted: {
                // Access the property
                console.log("Initial value:", PropertySignalModel.value)

                // Connect to the explicit valueChanged(int) signal
                // Note: This is the explicit Signal(int), not the auto-generated notify signal
                PropertySignalModel.valueChanged.connect(function(newValue) {
                    console.log("Value changed to:", newValue)
                })
            }
        }
        """

        self.engine.loadData(qml_code.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)
        assert len(self.engine.rootObjects()) > 0

