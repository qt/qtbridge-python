# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

"""Tests for Polars DataFrame (Table) support in AutoQmlBridgeModel."""

import sys
import os
import tempfile

import pytest

polars = pytest.importorskip("polars", reason="polars not installed")

from PySide6.QtCore import Qt, QUrl, qInstallMessageHandler, QModelIndex
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import bridge_instance, bridge_type, insert

class BridgeTypeBasic:
    """Provides a pre-populated DataFrame for bridge_type basic tests."""

    def __init__(self):
        self._df = polars.DataFrame({"name": ["Alice", "Bob"], "score": [95, 87]})

    def data(self) -> polars.DataFrame:
        return self._df


class BridgeTypeInsert:
    """Starts with an empty DataFrame; rows are added via @insert."""

    def __init__(self):
        self._df = polars.DataFrame(
            {"name": polars.Series([], dtype=polars.Utf8),
             "score": polars.Series([], dtype=polars.Int64)}
        )

    def data(self) -> polars.DataFrame:
        return self._df

    @insert
    def add_row(self, name: str, score: int):
        self._df = polars.concat(
            [self._df, polars.DataFrame({"name": [name], "score": [score]})]
        )


class PolarsModel:
    """Model that returns a Polars DataFrame via data()."""

    def __init__(self, df: polars.DataFrame):
        self._df = df

    def data(self) -> polars.DataFrame:
        return self._df


class PolarsModelTypeHinted:
    """Model with a polars.DataFrame return type-hint on data()."""

    def __init__(self):
        self._df = polars.DataFrame({
            "x": [1, 2],
            "y": [3, 4],
        })

    def data(self) -> polars.DataFrame:
        return self._df

class TestTableData:
    """Verify DataFrame → multi-column QAIM mapping."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured_messages: list[str] = []

    def teardown_method(self):
        if self.engine:
            del self.engine
            self.engine = None
        qInstallMessageHandler(None)

    def message_handler(self, msg_type, context, message):
        self.captured_messages.append(message)

    def test_row_count(self, qtbot, tmp_path):
        """rowCount() should equal the number of DataFrame rows."""
        df = polars.DataFrame({"a": [10, 20, 30], "b": [1, 2, 3]})
        model = PolarsModel(df)
        bridge_instance(model, name="RowCountModel")

        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("ROWS=" + RowCountModel.rowCount())
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        assert any("ROWS=3" in m for m in self.captured_messages), \
            f"Expected ROWS=3, got: {self.captured_messages}"

    def test_column_count(self, qtbot, tmp_path):
        """columnCount() should equal the number of DataFrame columns."""
        df = polars.DataFrame({"x": [1], "y": [2], "z": [3]})
        model = PolarsModel(df)
        bridge_instance(model, name="ColCountModel")

        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("COLS=" + ColCountModel.columnCount())
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        assert any("COLS=3" in m for m in self.captured_messages), \
            f"Expected COLS=3, got: {self.captured_messages}"


    def test_display_role_access(self, qtbot, tmp_path):
        """TableView-style column access via Qt::DisplayRole should return correct values."""
        df = polars.DataFrame({
            "name": ["Alice", "Bob"],
            "score": [95, 87],
        })
        model = PolarsModel(df)
        bridge_instance(model, name="DisplayModel")

        # Access first row, each column via TableView delegate (display role)
        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        // Qt::DisplayRole == 0
        console.log("NAME0=" + DisplayModel.data(DisplayModel.index(0, 0), 0))
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        # The display role (0) for column 0 should return "Alice"
        assert any("NAME0=Alice" in m for m in self.captured_messages), \
            f"Expected NAME0=Alice, got: {self.captured_messages}"

    def test_role_based_access(self, qtbot, tmp_path):
        """Role data (DataFrame columns) should be accessible via the model API.
        """
        df = polars.DataFrame({
            "city": ["Paris", "Tokyo"],
            "pop": [2_161_000, 13_960_000],
        })
        model = PolarsModel(df)
        bridge_instance(model, name="RoleModel")

        # Col 0 = "city": row 0 → "Paris", row 1 → "Tokyo"
        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("CITY=" + RoleModel.data(RoleModel.index(0, 0)))
        console.log("CITY=" + RoleModel.data(RoleModel.index(1, 0)))
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        assert any("Paris" in m for m in self.captured_messages)
        assert any("Tokyo" in m for m in self.captured_messages)

    def test_empty_dataframe(self, qtbot, tmp_path):
        """An empty DataFrame should produce a model with 0 rows but correct columns."""
        df = polars.DataFrame({"a": [], "b": []}).cast({"a": polars.Int64, "b": polars.Int64})
        model = PolarsModel(df)
        bridge_instance(model, name="EmptyModel")

        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("EMPTY_ROWS=" + EmptyModel.rowCount())
        console.log("EMPTY_COLS=" + EmptyModel.columnCount())
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        assert any("EMPTY_ROWS=0" in m for m in self.captured_messages), \
            f"Expected EMPTY_ROWS=0, got: {self.captured_messages}"
        assert any("EMPTY_COLS=2" in m for m in self.captured_messages), \
            f"Expected EMPTY_COLS=2, got: {self.captured_messages}"

    def test_mixed_dtypes(self, qtbot, tmp_path):
        """DataFrame with mixed dtypes (str, int, float, bool) should convert correctly."""
        df = polars.DataFrame({
            "label": ["X"],
            "count": [42],
            "ratio": [3.14],
            "flag":  [True],
        })
        model = PolarsModel(df)
        bridge_instance(model, name="DtypeModel")

        # Col 0=label, 1=count, 2=ratio, 3=flag — single row (row 0).
        # Repeater is intentionally avoided; see test_role_based_access docstring.
        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("LABEL=" + DtypeModel.data(DtypeModel.index(0, 0)))
        console.log("COUNT=" + DtypeModel.data(DtypeModel.index(0, 1)))
        console.log("RATIO=" + DtypeModel.data(DtypeModel.index(0, 2)))
        console.log("FLAG=" + DtypeModel.data(DtypeModel.index(0, 3)))
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        assert any("LABEL=X" in m for m in self.captured_messages), \
            f"Expected LABEL=X, got: {self.captured_messages}"
        assert any("COUNT=42" in m for m in self.captured_messages), \
            f"Expected COUNT=42, got: {self.captured_messages}"
        # float comparison: 3.14 should appear
        assert any("RATIO=3.14" in m for m in self.captured_messages), \
            f"Expected RATIO=3.14, got: {self.captured_messages}"
        assert any("FLAG=true" in m for m in self.captured_messages), \
            f"Expected FLAG=true, got: {self.captured_messages}"

    def test_method_callable(self, qtbot, tmp_path):
        """Methods on the model class should remain callable from QML."""

        class TableWithMethod:
            def __init__(self):
                self._df = polars.DataFrame({"v": [1, 2, 3]})

            def data(self) -> polars.DataFrame:
                return self._df

            def total(self) -> int:
                return int(self._df["v"].sum())

        model = TableWithMethod()
        bridge_instance(model, name="MethodModel")

        qml = """
import QtQuick 2.0
import backend 1.0

Item {
    Component.onCompleted: {
        console.log("TOTAL=" + MethodModel.total())
    }
}
"""
        qml_file = tmp_path / "test.qml"
        qml_file.write_text(qml)
        qInstallMessageHandler(self.message_handler)
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        qtbot.waitUntil(lambda: bool(self.engine.rootObjects()))

        assert any("TOTAL=6" in m for m in self.captured_messages), \
            f"Expected TOTAL=6, got: {self.captured_messages}"


class TestBridgeTypeTable:
    """Verify bridge_type() + polars DataFrame support."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()
        self.captured_messages: list[str] = []

    def teardown_method(self):
        if self.engine:
            del self.engine
            self.engine = None
        qInstallMessageHandler(None)

    def message_handler(self, msg_type, context, message):
        self.captured_messages.append(message)

    def test_bridge_type_row_and_column_count(self, qtbot):
        """QML-instantiated bridge_type model should report correct row/column counts."""

        bridge_type(BridgeTypeBasic, uri="backend_bt", version="1.0")

        qml = """
import QtQuick 2.0
import backend_bt 1.0

Item {
    BridgeTypeBasic { id: m }
    Component.onCompleted: {
        console.log("BT_ROWS=" + m.rowCount())
        console.log("BT_COLS=" + m.columnCount())
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml.encode(), QUrl())
        qtbot.wait(200)

        assert any("BT_ROWS=2" in m for m in self.captured_messages), \
            f"Expected BT_ROWS=2, got: {self.captured_messages}"
        assert any("BT_COLS=2" in m for m in self.captured_messages), \
            f"Expected BT_COLS=2, got: {self.captured_messages}"

    def test_bridge_type_display_role(self, qtbot):
        """DisplayRole access should work on bridge_type + polars."""

        bridge_type(BridgeTypeBasic, uri="backend_bt", version="1.0")

        qml = """
import QtQuick 2.0
import backend_bt 1.0

Item {
    BridgeTypeBasic { id: m }
    Component.onCompleted: {
        // Qt::DisplayRole == 0
        console.log("BT_NAME0=" + m.data(m.index(0, 0), 0))
        console.log("BT_SCORE0=" + m.data(m.index(0, 1), 0))
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml.encode(), QUrl())
        qtbot.wait(200)

        assert any("BT_NAME0=Alice" in m for m in self.captured_messages), \
            f"Expected BT_NAME0=Alice, got: {self.captured_messages}"
        assert any("BT_SCORE0=95" in m for m in self.captured_messages), \
            f"Expected BT_SCORE0=95, got: {self.captured_messages}"

    def test_bridge_type_insert_updates_model(self, qtbot):
        """@insert decorator should grow the DataFrame and update rowCount/data."""

        bridge_type(BridgeTypeInsert, uri="backend_bt", version="1.0")

        qml = """
import QtQuick 2.0
import backend_bt 1.0

Item {
    BridgeTypeInsert { id: m }
    Component.onCompleted: {
        m.add_row("Carol", 77)
        console.log("BT_INS_ROWS=" + m.rowCount())
        console.log("BT_INS_NAME0=" + m.data(m.index(0, 0), 0))
        console.log("BT_INS_SCORE0=" + m.data(m.index(0, 1), 0))
    }
}
"""
        qInstallMessageHandler(self.message_handler)
        self.engine.loadData(qml.encode(), QUrl())
        qtbot.wait(200)

        assert any("BT_INS_ROWS=1" in m for m in self.captured_messages), \
            f"Expected BT_INS_ROWS=1, got: {self.captured_messages}"
        assert any("BT_INS_NAME0=Carol" in m for m in self.captured_messages), \
            f"Expected BT_INS_NAME0=Carol, got: {self.captured_messages}"
        assert any("BT_INS_SCORE0=77" in m for m in self.captured_messages), \
            f"Expected BT_INS_SCORE0=77, got: {self.captured_messages}"
