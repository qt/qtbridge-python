# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance

import pytest


class UserDataModel:
    def __init__(self):
        self._data = [
            {"name": "Oliver", "age": 27, "city": "Vienna", "profession": "Mechanical Engineer"},
            {"name": "Mia", "age": 22, "city": "Lisbon", "profession": "Computer Science Student"},
            {"name": "Lucas", "age": 38, "city": "Zurich", "profession": "Financial Consultant"},
            {"name": "Ava", "age": 26, "city": "Copenhagen", "profession": "UX Researcher"},
            {"name": "Sophia", "age": 24, "city": "Madrid", "profession": "Graphic Designer"},
        ]

    def data(self) -> list[dict]:
        return self._data


class TestBridgeInstanceDictList:
    """Test bridge_instance() functionality with different scenarios of DataType DictList"""

    def setup_method(self):
        """Setup that runs before each test method"""
        self.engine = QQmlApplicationEngine()
        self.captured_messages = []

    def teardown_method(self):
        """Cleanup after each test method"""
        if self.engine:
            del self.engine
            self.engine = None
        qInstallMessageHandler(None)
        self.captured_messages.clear()

    def message_handler(self, msg_type, context, message):
        """Capture console messages from QML"""
        self.captured_messages.append(message)

    def get_console_messages(self):
        """Get all captured console messages"""
        return [msg for msg in self.captured_messages if not msg.startswith("qml:")]

    def test_list_dict(self, qtbot):
        """Test list[dict] functionality"""

        model = UserDataModel()
        bridge_instance(model, name="UserData")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("User Count:", UserData.rowCount())
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(100)

        messages = self.get_console_messages()
        assert any("User Count: 5" in msg for msg in messages), \
            f"Expected 'User Count: 5' message. Got: {messages}"

    def test_list_dict_access(self, qtbot):
        """Test accessing dict fields in ListView"""

        model = UserDataModel()
        bridge_instance(model, name="UserData")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    width: 400
    height: 300
    ListView {
        id: listView
        anchors.fill: parent
        model: UserData

        delegate: Item {
            Component.onCompleted: {
                console.log("User:",
                model.name,
                model.age,
                model.city,
                model.profession)
            }
        }
    }
    Component.onCompleted: {
        console.log("User Data count:", UserData.rowCount())
    }
}
"""

        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(200)

        messages = self.get_console_messages()

        assert any("User: Oliver 27 Vienna Mechanical Engineer" in msg for msg in messages), \
            f"Expected 'User: Oliver 27 Vienna Mechanical Engineer' message. Got: {messages}"
        assert any("User: Mia 22 Lisbon Computer Science Student" in msg for msg in messages), \
            f"Expected 'User: Mia 22 Lisbon Computer Science Student' message. Got: {messages}"
        assert any("User: Lucas 38 Zurich Financial Consultant" in msg for msg in messages), \
            f"Expected 'User: Lucas 38 Zurich Financial Consultant' message. Got: {messages}"
        assert any("User: Ava 26 Copenhagen UX Researcher" in msg for msg in messages), \
            f"Expected 'User: Ava 26 Copenhagen UX Researcher' message. Got: {messages}"
        assert any("User: Sophia 24 Madrid Graphic Designer" in msg for msg in messages), \
            f"Expected 'User: Sophia 24 Madrid Graphic Designer' message. Got: {messages}"
        assert any("User Data count: 5" in msg for msg in messages), \
            f"Expected 'User Data Count 5' message. Got: {messages}"

    def test_list_dict_mixed_keys(self, qtbot):
        """Test dict list where dicts have different keys"""
        class MixedKeysModel:
            def __init__(self):
                self._data = [
                    {"name": "Item1", "value": 100},
                    {"name": "Item2", "price": 200},  # Different key
                    {"title": "Item3", "value": 300},  # Different key
                ]

            def data(self) -> list[dict]:
                return self._data

        model = MixedKeysModel()

        try:
            bridge_instance(model, name="MixedKeys")
        except Exception as e:
            assert False, pytest.fail(f"bridge_instance failed with mixed keys: {e}")

    def test_list_dict_nested_dict(self, qtbot):
        """Test dict list with nested dictionaries"""
        class NestedDictModel:
            def __init__(self):
                self._data = [
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

            def data(self) -> list[dict]:
                return self._data

        model = NestedDictModel()
        bridge_instance(model, name="NestedData")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    width: 400
    height: 300
    ListView {
        id: listView
        anchors.fill: parent
        model: NestedData
        delegate: Item {
            Component.onCompleted: {
                console.log("User:",
                model.name,
                model.age,
                model.address.city,
                model.address.country)
            }
        }
    }
    Component.onCompleted: {
        console.log("Nested Data Count:", NestedData.rowCount())
    }
}
"""

        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(200)

        messages = self.get_console_messages()

        assert any("User: Liam 34 Amsterdam Netherlands" in msg for msg in messages), \
            f"Expected 'User: Liam 34 Amsterdam Netherlands' message. Got: {messages}"
        assert any("User: Sophia 27 Barcelona Spain" in msg for msg in messages), \
            f"Expected 'User: Sophia 27 Barcelona Spain' message. Got: {messages}"
        assert any("User: Noah 41 Toronto Canada" in msg for msg in messages), \
            f"Expected 'User: Noah 41 Toronto Canada' message. Got: {messages}"
        assert any("Nested Data Count: 3" in msg for msg in messages), \
            f"Expected 'Nested Data Count 3' message. Got: {messages}"

    def test_list_dict_various_types(self, qtbot):
        """Test dict with various value types (str, int, float, bool, list)"""
        class VariousTypesModel:
            def __init__(self):
                self._data = [
                    {
                        "name": "Item",
                        "count": 42,
                        "price": 99.99,
                        "active": True,
                        "tags": ["tag1", "tag2"]
                    }
                ]

            def data(self) -> list[dict]:
                return self._data

        model = VariousTypesModel()
        bridge_instance(model, name="VariousTypes")

        qml_content = """
import QtQuick 2.15
import backend 1.0

Item {
    width: 400
    height: 300
    ListView {
        id: listView
        anchors.fill: parent
        model: VariousTypes
        delegate: Item {
            Component.onCompleted: {
                console.log("Name:", model.name,
                "Count:", model.count,
                "Price:", model.price,
                "Active:", model.active,
                "Tags:", model.tags)
            }
        }
    }
}
"""

        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml_content.encode(), QUrl())
        qtbot.wait(200)

        messages = self.get_console_messages()

        assert any("Name: Item" in msg for msg in messages), \
            f"Expected 'Name: Item' message. Got: {messages}"
        assert any("Count: 42" in msg for msg in messages), \
            f"Expected 'Count: 42' message. Got: {messages}"
        assert any("Active: true" in msg for msg in messages), \
            f"Expected 'Active: true' message. Got: {messages}"
        assert any("Tags: [tag1,tag2]" in msg for msg in messages), \
            f"Expected 'Tags: [tag1,tag2]' message. Got: {messages}"
        # assert any("Int: 42 number" in msg for msg in messages), \
        #     f"Expected int type. Got: {messages}"

    def test_list_dict_special_characters(self, qtbot):
        """Test dict keys with special characters"""
        class SpecialCharModel:
            def __init__(self):
                self._data = [
                    {
                        "1": "User1",           # Numeric Key
                        "user-name": "John",    # Special Character
                        "email_address": "john@example.com",  # Unicode Character
                    }
                ]

            def data(self) -> list[dict]:
                return self._data

        model = SpecialCharModel()
        try:
            bridge_instance(model, name="SpecialChars")
        except Exception as e:
            assert False, pytest.fail(f"bridge_instance failed with special characters: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
