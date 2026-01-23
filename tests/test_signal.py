# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, Signal

import pytest


TEST_QML_CONNECT_JS = """
import QtQuick 2.0
import backend 1.0

Item {
    property int jsReceivedCount: 0
    property int jsLastValue: 0

    Component.onCompleted: {
        // Test connecting to JavaScript function
        SignalTestModel.valueChanged.connect(function(value) {
            console.log("JS: Signal received:", value)
            jsReceivedCount++
            jsLastValue = value
        })

        // Trigger signal emission
        SignalTestModel.setValue(42)
        SignalTestModel.setValue(100)
    }
}
"""

TEST_QML_DISCONNECT_JS = """
import QtQuick 2.0
import backend 1.0

Item {
    property int jsReceivedCount: 0
    property var jsHandler

    Component.onCompleted: {
        jsHandler = function(value) {
            console.log("JS: Signal received:", value)
            jsReceivedCount++
        }

        // Connect
        SignalTestModel.valueChanged.connect(jsHandler)
        SignalTestModel.setValue(10)

        // Disconnect
        SignalTestModel.valueChanged.disconnect(jsHandler)
        SignalTestModel.setValue(20)

        console.log("JS: Final count:", jsReceivedCount)
    }
}
"""

TEST_QML_EMIT_TEST = """
import QtQuick 2.0
import backend 1.0

Item {
    property int jsReceivedCount: 0
    property int jsLastValue: 0

    Component.onCompleted: {
        SignalTestModel.valueChanged.connect(function(value) {
            console.log("JS: Emit test received:", value)
            jsReceivedCount++
            jsLastValue = value
        })

        // Test explicit emit
        SignalTestModel.emitSignal(999)
    }
}
"""

TEST_QML_PROPERTY_SIGNAL = """
import QtQuick 2.0
import backend 1.0

Item {
    property int jsCallbackCount: 0
    property int jsLastValue: 0

    Component.onCompleted: {
        // Connect to the valueChanged(int) signal
        SignalTestModel.valueChanged.connect(function(newValue) {
            console.log("JS: Value changed to:", newValue)
            jsCallbackCount++
            jsLastValue = newValue
        })

        // Change the value to trigger the signal
        SignalTestModel.value = 100
    }
}
"""

TEST_QML_CONNECT_PYTHON_CALLABLE = """
import QtQuick 2.0
import backend 1.0

Item {
    property int emitCount: 0

    Component.onCompleted: {
        // Connect the signal to a Python method from QML
        SignalTestModel.valueChanged.connect(SignalTestModel.python_slot)

        // Emit signals to trigger the Python callable
        SignalTestModel.setValue(42)
        emitCount++
        SignalTestModel.setValue(100)
        emitCount++

        console.log("QML: Emitted", emitCount, "signals")
    }
}
"""


class SignalTestModel:
    """Test model with a Signal"""
    valueChanged = Signal(int)

    def __init__(self):
        self._value = 0
        self._python_callback_count = 0
        self._python_last_value = None

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int):
        """Property setter that emits signal"""
        if self._value != val:
            self._value = val
            self.valueChanged.emit(val)

    def setValue(self, value: int):
        """Set value and emit signal"""
        self._value = value
        self.valueChanged.emit(value)

    def emitSignal(self, value: int):
        """Explicitly emit signal for testing"""
        self.valueChanged.emit(value)

    def setup_python_connections(self):
        """Setup Python callbacks"""
        self.valueChanged.connect(self.python_callback)

    def python_callback(self, value: int):
        """Python callback for signal"""
        self._python_callback_count += 1
        self._python_last_value = value

    def python_slot(self, value: int):
        """Python slot that can be connected from QML"""
        self._python_callback_count += 1
        self._python_last_value = value

    def data(self):
        """Required method for QtBridge"""
        return [self._value]


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
        self.setup_message_capture()

        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        # Setup Python callback after bridge_instance
        model.setup_python_connections()

        self.engine.loadData(TEST_QML_PROPERTY_SIGNAL.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)

        root = self.engine.rootObjects()[0]
        messages = self.get_console_messages()

        # Verify QML callback was called
        assert root.property("jsCallbackCount") == 1, f"Expected JS callback once, got {root.property('jsCallbackCount')}"
        assert root.property("jsLastValue") == 100, f"Expected last value 100, got {root.property('jsLastValue')}"

        # Verify Python callback was called
        assert model._python_callback_count == 1, f"Expected Python callback once, got {model._python_callback_count}"

        # Verify console output
        assert any("JS: Value changed to: 100" in msg for msg in messages), "Signal with value 100 not received in JS"

        # Verify that auto-emission was skipped for the explicit Signal
        assert any("Skipping auto-emission for property" in msg and "value" in msg and "explicit Signal" in msg
                   for msg in messages), "Expected debug message about skipping auto-emission for explicit Signal"

    def test_signal_connect_to_qml_function(self, qtbot):
        """Test connecting a signal to a QML/JavaScript function"""
        self.setup_message_capture()

        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        self.engine.loadData(TEST_QML_CONNECT_JS.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)

        root = self.engine.rootObjects()[0]
        messages = self.get_console_messages()

        # Should receive both emitted signals
        assert root.property("jsReceivedCount") == 2, f"Expected 2 signals, got {root.property('jsReceivedCount')}"
        assert root.property("jsLastValue") == 100, f"Expected last value 100, got {root.property('jsLastValue')}"

        # Verify console output
        assert any("JS: Signal received: 42" in msg for msg in messages), "Signal with value 42 not received"
        assert any("JS: Signal received: 100" in msg for msg in messages), "Signal with value 100 not received"

    def test_signal_disconnect_from_qml_function(self, qtbot):
        """Test disconnecting a signal from a QML/JavaScript function"""
        self.setup_message_capture()

        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        self.engine.loadData(TEST_QML_DISCONNECT_JS.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)

        root = self.engine.rootObjects()[0]
        messages = self.get_console_messages()

        # Should receive only 1 signal (before disconnect)
        assert root.property("jsReceivedCount") == 1, f"Expected 1 signal (before disconnect), got {root.property('jsReceivedCount')}"

        # Verify only the first signal was received
        assert any("JS: Signal received: 10" in msg for msg in messages), "Signal with value 10 not received"
        assert not any("JS: Signal received: 20" in msg for msg in messages), "Signal with value 20 should NOT be received after disconnect"
        assert any("JS: Final count: 1" in msg for msg in messages), "Final count should be 1"

    def test_signal_emit_from_python(self, qtbot):
        """Test explicitly emitting a signal from Python"""
        self.setup_message_capture()

        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        self.engine.loadData(TEST_QML_EMIT_TEST.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)

        root = self.engine.rootObjects()[0]
        messages = self.get_console_messages()

        # Should receive the emitted signal
        assert root.property("jsReceivedCount") == 1, f"Expected 1 signal, got {root.property('jsReceivedCount')}"
        assert root.property("jsLastValue") == 999, f"Expected value 999, got {root.property('jsLastValue')}"

        # Verify console output
        assert any("JS: Emit test received: 999" in msg for msg in messages), "Signal with value 999 not received"

    def test_signal_connect_to_python_function(self, qtbot):
        """Test connecting a signal to a Python function"""
        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        model.setup_python_connections()

        # Emit signals
        model.setValue(42)
        model.setValue(100)

        # Verify Python callback was called
        assert model._python_callback_count == 2, f"Expected 2 callbacks, got {model._python_callback_count}"
        assert model._python_last_value == 100, f"Expected last value 100, got {model._python_last_value}"

    def test_signal_disconnect_from_python_function(self, qtbot):
        """Test disconnecting a signal from a Python function"""
        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        model.setup_python_connections()

        # Emit signal
        model.setValue(10)
        assert model._python_callback_count == 1, "First signal should be received"

        # Disconnect
        model.valueChanged.disconnect(model.python_callback)

        # Emit signal should NOT be received
        model.setValue(20)
        assert model._python_callback_count == 1, "Callback count should still be 1 after disconnect"
        assert model._python_last_value == 10, "Last value should still be 10 (from before disconnect)"

    def test_signal_connect_multiple_callbacks(self, qtbot):
        """Test connecting multiple Python callbacks to the same signal"""
        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        # Track calls
        callback1_count = [0]
        callback2_count = [0]

        def callback1(value):
            callback1_count[0] += 1

        def callback2(value):
            callback2_count[0] += 1

        # Connect both callbacks
        model.valueChanged.connect(callback1)
        model.valueChanged.connect(callback2)

        # Emit signal
        model.setValue(42)

        # Both callbacks should be called
        assert callback1_count[0] == 1, "Callback1 should be called once"
        assert callback2_count[0] == 1, "Callback2 should be called once"

        # Disconnect one callback
        model.valueChanged.disconnect(callback1)

        # Emit again
        model.setValue(100)

        # Only callback2 should be called
        assert callback1_count[0] == 1, "Callback1 should still be called once (disconnected)"
        assert callback2_count[0] == 2, "Callback2 should be called twice"

    def test_signal_lambda_connection(self, qtbot):
        """Test connecting a signal to a lambda function"""
        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        # Track lambda calls
        lambda_values = []

        # Connect lambda
        model.valueChanged.connect(lambda v: lambda_values.append(v))

        # Emit signals
        model.setValue(1)
        model.setValue(2)
        model.setValue(3)

        # Verify lambda was called with correct values
        assert lambda_values == [1, 2, 3], f"Expected [1, 2, 3], got {lambda_values}"

    def test_signal_connect_to_python_callable_from_qml(self, qtbot):
        """Test connecting a signal to a Python callable from QML"""
        self.setup_message_capture()

        model = SignalTestModel()
        bridge_instance(model, name="SignalTestModel")

        self.engine.loadData(TEST_QML_CONNECT_PYTHON_CALLABLE.encode(), QUrl())
        qtbot.waitUntil(lambda: len(self.engine.rootObjects()) > 0, timeout=5000)

        root = self.engine.rootObjects()[0]
        messages = self.get_console_messages()

        assert model._python_callback_count == 2, f"Expected 2 Python callbacks, got {model._python_callback_count}"
        assert model._python_last_value == 100, f"Expected last value 100, got {model._python_last_value}"

        assert root.property("emitCount") == 2, f"Expected 2 emits from QML, got {root.property('emitCount')}"

        assert any("QML: Emitted 2 signals" in msg for msg in messages), "Expected console message about emitting signals"
