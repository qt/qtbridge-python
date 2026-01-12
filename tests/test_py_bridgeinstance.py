# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

from qtbridge_py.autoqmlbridge import bridge_instance, _bridge_map

import numpy as np
import pytest

TEST_QML_METHOD = """
import QtQuick 2.0
import backend 1.0

Item {
    width: 100
    height: 100

    Component.onCompleted: {
        console.log("Model count:", Test_model.rowCount())
    }
}
"""


class TestAutoQmlBridge:
    """Test bridge_instance() method with python containers"""

    def test_bridge_instance_with_list(self, qtbot, tmp_path):
        """Test that bridge_instance registers a QRangeModel for list objects."""
        test_list = [1, 2, 3]
        bridge_instance(test_list, name="Test_model")

        engine = QQmlApplicationEngine()

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        # Load QML
        engine.load(QUrl.fromLocalFile(str(qml_file)))

        # Wait for QML to load
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 3
        assert model.data(model.index(0, 0)) == 1
        assert model.data(model.index(1, 0)) == 2
        assert model.data(model.index(2, 0)) == 3

    def test_bridge_instance_with_tuple(self, qtbot, tmp_path):
        """Test that bridge_instance registers a QRangeModel for list objects."""
        test_tuple = ("apple", "orange", "grape", "banana")
        bridge_instance(test_tuple, "Test_model")

        engine = QQmlApplicationEngine()

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        # Load QML
        engine.load(QUrl.fromLocalFile(str(qml_file)))

        # Wait for QML to load
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 4
        assert model.data(model.index(0, 0)) == "apple"
        assert model.data(model.index(1, 0)) == "orange"
        assert model.data(model.index(2, 0)) == "grape"
        assert model.data(model.index(3, 0)) == "banana"

    def test_bridge_instance_with_numpy_array(self, qtbot, tmp_path):
        """Test that bridge_instance registers a QRangeModel for numpy arrays."""
        test_array = np.array([[10, 20], [30, 40]])
        bridge_instance(test_array, "Test_model")

        engine = QQmlApplicationEngine()

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(TEST_QML_METHOD)

        engine.load(QUrl.fromLocalFile(str(qml_file)))

        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 2
        assert model.data(model.index(0, 0)) == 10
        assert model.data(model.index(0, 1)) == 20
        assert model.data(model.index(1, 0)) == 30
        assert model.data(model.index(1, 1)) == 40
