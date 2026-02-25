# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

from qtbridge_py.autoqmlbridge import bridge_instance, _bridge_map

import numpy as np
import pytest


QML_TEMPLATE = """
import QtQuick 2.0
import backend 1.0

Item {
    width: 100
    height: 100

    Component.onCompleted: {
        console.log("Model count:", PyModel.rowCount())
    }
}
"""


@pytest.mark.forked
class TestAutoQmlBridge:
    """Test bridge_instance() method with python containers.

    Each test is forked into a separate subprocess to work around a possible 
    bug in either Qt/PySide6 where calling qmlRegisterSingletonInstance(QRangeModel, ...) 
    two or more times in the same process corrupts Qt's global QQmlMetaType registry.

    Root cause:
        bridge_instance() calls qmlRegisterSingletonInstance(QRangeModel, ...)
        to expose a Python list/tuple/array to QML.  After a second such call
        (even with a different URI/name), QQmlMetaType::metaObjectForType()
        silently fails to return a valid QMetaObject* for subsequently
        registered bridge_type() types.

    Workaround:
        @pytest.mark.forked gives each test a clean forked subprocess with a
        fresh QQmlMetaType registry, so only one QRangeModel registration
        ever occurs per process.
    """

    def test_bridge_instance_with_list(self, qtbot, tmp_path):
        """Test that bridge_instance registers a QRangeModel for list objects."""
        test_list = [1, 2, 3]
        bridge_instance(test_list, name="PyModel")

        engine = QQmlApplicationEngine()

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

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

        del engine

    def test_bridge_instance_with_tuple(self, qtbot, tmp_path):
        """Test that bridge_instance registers a QRangeModel for tuple objects."""
        test_tuple = ("apple", "orange", "grape", "banana")
        bridge_instance(test_tuple, name="PyModel")

        engine = QQmlApplicationEngine()

        # Write QML to temporary file
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

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

        del engine

    def test_bridge_instance_with_numpy_array(self, qtbot, tmp_path):
        """Test that bridge_instance registers a QRangeModel for numpy arrays."""
        test_array = np.array([[10, 20], [30, 40]])
        bridge_instance(test_array, name="PyModel")

        engine = QQmlApplicationEngine()

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

        engine.load(QUrl.fromLocalFile(str(qml_file)))

        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 2
        assert model.data(model.index(0, 0)) == 10
        assert model.data(model.index(0, 1)) == 20
        assert model.data(model.index(1, 0)) == 30
        assert model.data(model.index(1, 1)) == 40

        del engine
