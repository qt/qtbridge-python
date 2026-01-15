# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import pytest
import os
import tempfile
from PySide6.QtCore import QUrl, qInstallMessageHandler, QtMsgType
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance

class TestErrorHandling:
    """Test error handling and logging behavior for both user errors and system errors"""
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
            'category': context.category if hasattr(context, 'category') else '',
            'message': message
        })

    def setup_message_capture(self):
        """Setup message capture for Qt logging"""
        self.captured_messages.clear()
        qInstallMessageHandler(self.message_handler)

    def get_qtbridge_messages(self, msg_type=None):
        """Get messages from QtBridges category, optionally filtered by type"""
        messages = [msg for msg in self.captured_messages
                   if 'qtbridges' in msg.get('category', '')]
        if msg_type is not None:
            messages = [msg for msg in messages if msg['type'] == msg_type]
        return messages

    def test_no_data_method(self, qtbot):
        """Test that error is raised when data() method is missing"""

        class AutoQmlBridgeTest:
            def __init__(self):
                self._strings = []

            def add_string(self, new_string: str) -> bool:
                self._strings.append(new_string)
                return True

            def data(self):
                return self._strings

        original_data_method = AutoQmlBridgeTest.data
        del AutoQmlBridgeTest.data
        try:
            with pytest.raises(
                TypeError,
                match=r"The class wrapped with bridge_instance must have a data\(\) method"
            ):
                bridge_instance(AutoQmlBridgeTest(), name="TestModel")
        finally:
            AutoQmlBridgeTest.data = original_data_method

    def test_system_error_critical_logging(self, qtbot):
        """Test that system errors generate critical log messages"""
        self.setup_message_capture()

        class SystemErrorModel:
            def __init__(self):
                self._items = ["item1"]

            def cause_system_error(self) -> str:
                raise RuntimeError("Simulated Runtime failure")

            def data(self):
                return self._items

        model = SystemErrorModel()
        bridge_instance(model, name="SystemErrorModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0

        Item {
            Component.onCompleted: {
                // This should trigger a RuntimeError
                SystemErrorModel.cause_system_error()
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name

        try:
            with pytest.raises(RuntimeError, match="Simulated Runtime failure"):
                self.engine.load(QUrl.fromLocalFile(qml_path))
                qtbot.waitUntil(lambda: bool(self.engine.rootObjects()), timeout=2000)
            qtbot.wait(100)

            warning_messages = self.get_qtbridge_messages(QtMsgType.QtWarningMsg)
            critical_messages = self.get_qtbridge_messages(QtMsgType.QtCriticalMsg)

            # Should have critical messages for RuntimeError
            system_error_criticals = [msg for msg in critical_messages
                                    if 'RuntimeError' in msg['message'] or 'Simulated Runtime failure' in msg['message']]
            assert len(system_error_criticals) > 0, f"Expected critical messages for system error, got: {critical_messages}"

            # RuntimeError should NOT be treated as user error (logged as warning)
            runtime_warnings = [msg for msg in warning_messages
                              if 'RuntimeError' in msg['message']]
            assert len(runtime_warnings) == 0, f"System errors should not generate warning messages, got: {runtime_warnings}"

        finally:
            os.unlink(qml_path)

    def test_user_error_types_are_warnings(self, qtbot):
        """Test that all user error types (ValueError, TypeError, etc.) generate warnings"""
        self.setup_message_capture()

        class UserErrorsModel:
            def __init__(self):
                self._items = ["item1", "item2"]

            def cause_value_error(self) -> str:
                raise ValueError("Invalid value provided by user")

            def cause_type_error(self) -> str:
                raise TypeError("Wrong type provided by user")

            def cause_attribute_error(self) -> str:
                raise AttributeError("Attribute not found")

            def cause_key_error(self) -> str:
                raise KeyError("Key not found in user data")

            def cause_index_error(self) -> str:
                raise IndexError("Index out of range")

            def data(self):
                return self._items

        model = UserErrorsModel()
        bridge_instance(model, name="UserErrorsModel")

        # Test each user error type
        error_methods = [
            "cause_value_error",
            "cause_type_error",
            "cause_attribute_error",
            "cause_key_error",
            "cause_index_error"
        ]

        for method_name in error_methods:
            self.captured_messages.clear()  # Clear for each test

            qml_content = f"""
            import QtQuick 2.0
            import backend 1.0

            Item {{
                Component.onCompleted: {{
                    UserErrorsModel.{method_name}()
                }}
            }}
            """

            with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
                f.write(qml_content)
                qml_path = f.name

            try:
                error_map = {
                    "cause_value_error": (ValueError, "Invalid value provided by user"),
                    "cause_type_error": (TypeError, "Wrong type provided by user"),
                    "cause_attribute_error": (AttributeError, "Attribute not found"),
                    "cause_key_error": (KeyError, "Key not found in user data"),
                    "cause_index_error": (IndexError, "Index out of range"),
                }
                exc_type, exc_msg = error_map[method_name]
                with pytest.raises(exc_type, match=exc_msg):
                    self.engine.load(QUrl.fromLocalFile(qml_path))
                    qtbot.waitUntil(lambda: bool(self.engine.rootObjects()), timeout=2000)

                # Check that this specific error type generates warnings
                warning_messages = self.get_qtbridge_messages(QtMsgType.QtWarningMsg)
                critical_messages = self.get_qtbridge_messages(QtMsgType.QtCriticalMsg)

                print(f"Captured warning messages for {method_name}: {warning_messages}")
                print(f"Captured critical messages for {method_name}: {critical_messages}")

                # Should have warnings for user errors
                method_warnings = [msg for msg in warning_messages
                                 if (msg.get('category') == 'qtbridges' and
                                     (method_name in msg['message'] or
                                      any(error_type in msg['message'] for error_type in
                                          ['ValueError', 'TypeError', 'AttributeError', 'KeyError', 'IndexError']) or
                                      'Invalid value provided by user' in msg['message'] or
                                      'Python method:' in msg['message']))]
                assert len(method_warnings) > 0, f"Expected warning for {method_name}, got warnings: {warning_messages}"

                # Should NOT have critical messages for user errors
                method_criticals = [msg for msg in critical_messages
                                  if method_name in msg['message']]
                assert len(method_criticals) == 0, f"User error {method_name} should not generate critical messages, got: {method_criticals}"

            finally:
                os.unlink(qml_path)

    def test_system_error_types_are_critical(self, qtbot):
        """Test that system error types (not in shouldSuppressError) generate critical messages"""
        self.setup_message_capture()

        class SystemErrorsModel:
            def __init__(self):
                self._items = ["item1"]

            def cause_runtime_error(self) -> str:
                raise RuntimeError("Database connection failed")

            def cause_memory_error(self) -> str:
                raise MemoryError("Out of memory")

            def cause_os_error(self) -> str:
                raise OSError("File system error")

            def cause_import_error(self) -> str:
                raise ImportError("Module not found")

            def data(self):
                return self._items

        model = SystemErrorsModel()
        bridge_instance(model, name="SystemErrorsModel")

        # Test each system error type
        error_methods = [
            "cause_runtime_error",
            "cause_memory_error",
            "cause_os_error",
            "cause_import_error"
        ]

        for method_name in error_methods:
            self.captured_messages.clear()

            qml_content = f"""
            import QtQuick 2.0
            import backend 1.0

            Item {{
                Component.onCompleted: {{
                    SystemErrorsModel.{method_name}()
                }}
            }}
            """

            with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
                f.write(qml_content)
                qml_path = f.name

            try:
                error_map = {
                    "cause_runtime_error": (RuntimeError, "Database connection failed"),
                    "cause_memory_error": (MemoryError, "Out of memory"),
                    "cause_os_error": (OSError, "File system error"),
                    "cause_import_error": (ImportError, "Module not found"),
                }
                exc_type, exc_msg = error_map[method_name]
                with pytest.raises(exc_type, match=exc_msg):
                    self.engine.load(QUrl.fromLocalFile(qml_path))
                    qtbot.waitUntil(lambda: bool(self.engine.rootObjects()), timeout=2000)

                # Check that this specific error type generates critical messages
                warning_messages = self.get_qtbridge_messages(QtMsgType.QtWarningMsg)
                critical_messages = self.get_qtbridge_messages(QtMsgType.QtCriticalMsg)

                # Should have critical messages for system errors
                method_criticals = [msg for msg in critical_messages
                                  if method_name in msg['message'] or
                                     any(error_type in msg['message'] for error_type in
                                         ['RuntimeError', 'MemoryError', 'OSError', 'ImportError'])]
                assert len(method_criticals) > 0, f"Expected critical message for {method_name}, got criticals: {critical_messages}"

                # Should NOT have warnings for system errors (they should be critical)
                method_warnings = [msg for msg in warning_messages
                                 if method_name in msg['message']]
                assert len(method_warnings) == 0, f"System error {method_name} should not generate warnings, got: {method_warnings}"

            finally:
                os.unlink(qml_path)

    def test_debug_vs_release_message_format(self, qtbot):
        """Test that debug builds show more detailed messages than release builds"""
        self.setup_message_capture()

        class TestModel:
            def __init__(self):
                self._items = ["test"]

            def cause_error(self) -> str:
                raise ValueError("Test error for format checking")

            def data(self):
                return self._items

        model = TestModel()
        bridge_instance(model, name="TestModel")

        qml_content = """
        import QtQuick 2.0
        import backend 1.0

        Item {
            Component.onCompleted: {
                TestModel.cause_error()
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
            f.write(qml_content)
            qml_path = f.name

        try:
            with pytest.raises(ValueError, match="Test error for format checking"):
                self.engine.load(QUrl.fromLocalFile(qml_path))
                qtbot.waitUntil(lambda: bool(self.engine.rootObjects()), timeout=2000)

            warning_messages = self.get_qtbridge_messages(QtMsgType.QtWarningMsg)

            assert len(warning_messages) > 0, "Expected warning message for ValueError"

            # Check if we're in debug build based on message content
            error_msg = warning_messages[0]['message']

            if 'Traceback' in error_msg or 'File "' in error_msg:
                print("DEBUG BUILD: Message includes traceback information")
                assert 'ValueError: Test error for format checking' in error_msg
            else:
                print(f'RELEASE BUILD: Message is simplified: "{error_msg}"')
                assert 'Test error for format checking' in error_msg

        finally:
            os.unlink(qml_path)

    def test_bridge_instance_infer_data_type_empty_data(self, qtbot):
        """Test that bridge_instance raises an error when data() has no type hint and
           returns empty list."""
        class EmptyModel:
            def data(self):
                pass

        with pytest.raises(TypeError) as excinfo:
            bridge_instance(EmptyModel(), name="EmptyModel")
        assert "Could not infer data type from data() method" in str(excinfo.value)

if __name__ == "__main__":
    pytest.main([__file__])
