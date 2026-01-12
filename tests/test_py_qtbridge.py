# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from PySide6.QtCore import QTimer, QCoreApplication, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine
import sys

from qtbridge_py.qtbridge import qtbridge

import pytest

TEST_QML_METHOD = """
import QtQuick 2.0

Item {
    width: 100
    height: 100

    Component.onCompleted: {
        console.log("QML Component completed!")
    }
}
"""


class TestQtBridge:
    """ Test qtbridge decorator. """

    def setup_method(self):
        """Setup for each test method"""
        self.captured_messages = []

    def message_handler(self, msg_type, context, message):
        """Capture console messages from QML"""
        self.captured_messages.append(message)

    def get_console_messages(self):
        """Get all captured console messages"""
        return [msg for msg in self.captured_messages if not msg.startswith("qml:")]

    def test_qtbridge_calls_wrapped_function(self, qtbot, tmp_path):
        """Test qtbridge calls the wrapped function."""
        dummy_set = {}

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        @qtbridge(qml_file=qml_file)
        def func_to_wrap():
            dummy_set["yes"] = True

        # schedule the app to exit with code 42
        QTimer.singleShot(0, lambda: QCoreApplication.exit(42))

        result = func_to_wrap()
        assert dummy_set.get("yes") is True
        assert result == 42

    def test_qtbridge_raises_if_no_qml_or_module(self, qtbot,):
        """Test qtbridge raises if there is no qml file or module passed."""
        @qtbridge()
        def dummy_func():
            pass

        with pytest.raises(ValueError, match="Either 'qml_file' or 'module' must be specified."):
            dummy_func()

    def test_qtbridge_loads_module(self, qtbot, tmp_path):
        """Test qtbridge loads module."""

        module_dir = tmp_path / "testPath" / "DummyModule"
        module_dir.mkdir(parents=True)
        (module_dir / "qmldir").write_text("dummyType 1.0 dummyType.qml\n")
        (module_dir / "dummyType.qml").write_text(TEST_QML_METHOD)

        sys.path.insert(0, str(tmp_path))

        @qtbridge(module="testPath.DummyModule", type_name="dummyType")
        def dummy_func():
            pass

        # schedule the app to exit with code 42
        QTimer.singleShot(0, lambda: QCoreApplication.exit(42))

        result = dummy_func()
        sys.path.remove(str(tmp_path))
        assert result == 42

    def test_qtbridge_loads_qml_relative_path(self, qtbot, tmp_path):
        """Test qtbridge loads qml file with relative path."""
        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        @qtbridge(qml_file=qml_file)
        def dummy_func():
            pass

        # schedule the app to exit with code 42
        QTimer.singleShot(0, lambda: QCoreApplication.exit(42))

        result = dummy_func()
        assert result == 42

    def test_qtbridge_loads_module_default_type(self, qtbot, tmp_path):
        """Test qtbridge loadFromModule('.', module) path is used."""

        # Create a fake QML module in a custom directory
        custom_import = tmp_path / "testPath"
        custom_import.mkdir()
        (custom_import / "qmldir").write_text("Dummy 1.0 Dummy.qml\n")
        (custom_import / "Dummy.qml").write_text(TEST_QML_METHOD)

        @qtbridge(module="Dummy", import_paths=[str(custom_import)])
        def dummy_func():
            pass

        # schedule the app to exit with code 42
        QTimer.singleShot(0, lambda: QCoreApplication.exit(42))

        result = dummy_func()
        assert result == 42

    def test_qtbridge_adds_import_paths(self, qtbot, tmp_path):
        """Test qtbridge adds custom import paths and uses type_name."""

        # Create a fake QML module in a custom directory
        custom_import = tmp_path / "testPath"
        module_dir = custom_import / "DummyModule"
        module_dir.mkdir(parents=True)

        (module_dir / "DummyType.qml").write_text(TEST_QML_METHOD)
        (module_dir / "qmldir").write_text("DummyType 1.0 DummyType.qml\n")

        @qtbridge(module="DummyModule", type_name="DummyType", import_paths=[str(custom_import)])
        def dummy_func():
            pass

        # schedule the app to exit with code 42
        QTimer.singleShot(0, lambda: QCoreApplication.exit(42))

        result = dummy_func()
        assert result == 42

    def test_qtbridge_qml_runs_on_completed(self, qtbot, tmp_path, capsys):
        """Test that QML application actually runs and Component.onCompleted is called."""

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        # Install message handler to capture console output
        qInstallMessageHandler(self.message_handler)

        @qtbridge(qml_file=qml_file)
        def dummy_func():
            pass

        # schedule the app to exit with code 42
        QTimer.singleShot(0, lambda: QCoreApplication.exit(42))

        result = dummy_func()
        # Verify the console output shows the default property assignment worked
        messages = self.get_console_messages()

        # Check that the console.log message appeared
        assert any("QML Component completed!" in m for m in messages), f"Messages: {messages}"
        assert result == 42
