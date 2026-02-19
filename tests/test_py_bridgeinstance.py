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

test_data = [
        {"name": "Oliver", "age": 27, "city": "Vienna", "profession": "Mechanical Engineer"},
        {"name": "Mia", "age": 22, "city": "Lisbon", "profession": "Computer Science Student"},
        {"name": "Lucas", "age": 38, "city": "Zurich", "profession": "Financial Consultant"},
        {"name": "Ava", "age": 26, "city": "Copenhagen", "profession": "UX Researcher"},
        {"name": "Sophia", "age": 24, "city": "Madrid", "profession": "Graphic Designer"},
    ]


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
        ever occurs per process. pytest-forked is only installed on Linux
        (see pyproject.toml), so the mark is a no-op on macOS and Windows.
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
        
    def test_bridge_instance_with_list_dict(self, qtbot, tmp_path):
        """Test bridge_instance with list[dict]"""

        bridge_instance(test_data, name="Test_model")

        engine = QQmlApplicationEngine()

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

        engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 5

    def test_bridge_instance_with_list_dict_access(self, qtbot, tmp_path):
        """Test bridge_instance accessing dict fields in ListView"""

        bridge_instance(test_data, name="Test_model")

        engine = QQmlApplicationEngine()

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

        engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 5

        for i, expected in enumerate(test_data):
            row_data = model.data(model.index(i, 0))

            # Assert all dict keys are present and accessible
            assert "name" in row_data
            assert "age" in row_data
            assert "city" in row_data
            assert "profession" in row_data

            # Assert values match
            assert row_data["name"] == expected["name"]
            assert row_data["age"] == expected["age"]
            assert row_data["city"] == expected["city"]
            assert row_data["profession"] == expected["profession"]

    def test_bridge_instance_with_list_dict_mixed_keys(self, qtbot, tmp_path):
        """Test bridge_instance with list[dict] where dicts have different keys"""

        mixed_keys = [
            {"name": "Item1", "value": 100},
            {"name": "Item2", "price": 200},  # Different key
            {"title": "Item3", "value": 300},  # Different key
        ]

        try:
            bridge_instance(mixed_keys, name="Test_model")
        except Exception as e:
            assert False, f"bridge_instance failed with mixed keys: {e}"

    def test_bridge_instance_with_list_dict_nested_dict(self, qtbot, tmp_path):
        """Test bridge_instance with nested dictionaries"""

        nested_data = [
            {
                "name": "Liam",
                "age": 34,
                "address": {"city": "Amsterdam", "country": "Netherlands"},
            },
            {
                "name": "Sophia",
                "age": 27,
                "address": {"city": "Barcelona", "country": "Spain"},
            },
            {
                "name": "Noah",
                "age": 41,
                "address": {"city": "Toronto", "country": "Canada"},
            },
        ]

        bridge_instance(nested_data, name="Test_model")

        engine = QQmlApplicationEngine()

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

        engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 3

        for i, expected in enumerate(nested_data):
            row_data = model.data(model.index(i, 0))

            # Assert all dict keys are present and accessible
            assert "name" in row_data
            assert "age" in row_data
            assert "address" in row_data
            assert "city" in row_data["address"]
            assert "country" in row_data["address"]

            # Assert values match
            assert row_data["name"] == expected["name"]
            assert row_data["age"] == expected["age"]
            assert row_data["address"] == expected["address"]
            assert row_data["address"]["city"] == expected["address"]["city"]
            assert row_data["address"]["country"] == expected["address"]["country"]

    def test_bridge_instance_with_list_dict_various_types(self, qtbot, tmp_path):
        """Test bridge_instance with dicts with various value types (str, int, float, bool, list)"""

        various_types = [
            {
                "name": "Item",
                "count": 42,
                "price": 99.99,
                "active": True,
                "tags": ["tag1", "tag2"]
            }
        ]

        bridge_instance(various_types, name="Test_model")

        engine = QQmlApplicationEngine()

        qml_file = tmp_path / "test.qml"
        qml_file.write_text(QML_TEMPLATE)

        engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(engine.rootObjects()))

        model = _bridge_map["model"]

        assert model is not None
        assert model.rowCount() == 1

        for i, expected in enumerate(various_types):
            row_data = model.data(model.index(i, 0))

            # Assert all dict keys are present and accessible
            assert "name" in row_data
            assert "count" in row_data
            assert "price" in row_data
            assert "active" in row_data
            assert "tags" in row_data

            # Assert values match
            assert row_data["name"] == expected["name"]
            assert row_data["count"] == expected["count"]
            assert row_data["price"] == expected["price"]
            assert row_data["active"] == expected["active"]
            assert row_data["tags"] == expected["tags"]

    def test_bridge_instance_with_list_dict_special_characters(self, qtbot):
        """Test dict keys with special characters"""

        special_char = [
            {
                "1": "User1",           # Numeric Key
                "user-name": "John",    # Special Character
                "email_address": "john@example.com",  # Unicode Character
            }
        ]

        try:
            bridge_instance(special_char, name="SpecialChars")
        except Exception as e:
            assert False, f"bridge_instance failed with special characters: {e}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
