# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
Iris Dataset CRUD — DuckDB + Polars + QtBridge

Port of the PySide6 pandas/dataframe_model example to Qt Quick, using:
  - **Polars** for the DataFrame exposed to QML (via QtBridge QAIM)
  - **DuckDB** as the in-process analytical database for CRUD operations
  - **QtBridge** decorators (@insert, @remove, @edit) for live model updates
"""

import sys
from pathlib import Path

import duckdb
import polars as pl

from QtBridge import bridge_instance, edit, insert, remove, qtbridge


class IrisModel:
    """Iris dataset backed by an in-memory DuckDB table.
    """

    def __init__(self):
        self._conn = duckdb.connect(":memory:")
        csv_path = str(Path(__file__).parent / "iris.csv")
        self._conn.execute(f"""
            CREATE TABLE iris AS
            SELECT
                row_number() OVER () AS id,
                "sepal.length" AS sepal_length,
                "sepal.width"  AS sepal_width,
                "petal.length" AS petal_length,
                "petal.width"  AS petal_width,
                lower(variety) AS species
            FROM read_csv_auto('{csv_path}')
        """)
        self._refresh()

    def _refresh(self):
        """Re-query DuckDB and cache the full result as a Polars DataFrame."""
        self._df = self._conn.execute(
            "SELECT * FROM iris ORDER BY id"
        ).pl()

    def data(self) -> pl.DataFrame:
        """Return the dataset *without* the internal ``id`` column."""
        return self._df.drop("id")

    def row_count(self) -> int:
        return len(self._df)

    def get_row(self, index: int) -> dict:
        """Return a single row as a dict (for pre-populating the edit dialog)."""
        if 0 <= index < len(self._df):
            row = self._df.row(index, named=True)
            return {k: v for k, v in row.items() if k != "id"}
        return {}

    @insert
    def add_row(self, sepal_length: float, sepal_width: float,
                petal_length: float, petal_width: float, species: str):
        """INSERT a new iris record into DuckDB."""
        next_id = self._conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM iris"
        ).fetchone()[0]
        self._conn.execute(
            "INSERT INTO iris VALUES (?, ?, ?, ?, ?, ?)",
            [next_id, sepal_length, sepal_width, petal_length, petal_width, species],
        )
        self._refresh()

    @remove
    def delete_row(self, index: int):
        """DELETE the row at *index* from DuckDB."""
        if 0 <= index < len(self._df):
            row_id = int(self._df[index, "id"])
            self._conn.execute("DELETE FROM iris WHERE id = ?", [row_id])
            self._refresh()
            return True
        return False

    @edit
    def update_row(self, index: int, sepal_length: float, sepal_width: float,
                   petal_length: float, petal_width: float, species: str):
        """UPDATE all fields of the row at *index* in DuckDB."""
        if 0 <= index < len(self._df):
            row_id = int(self._df[index, "id"])
            self._conn.execute("""
                UPDATE iris
                SET sepal_length = ?, sepal_width = ?,
                    petal_length = ?, petal_width = ?,
                    species = ?
                WHERE id = ?
            """, [sepal_length, sepal_width, petal_length, petal_width,
                  species, row_id])
            self._refresh()
            return True
        return False


@qtbridge(qml_file="Main.qml")
def main():
    model = IrisModel()
    bridge_instance(model, name="IrisData")


if __name__ == "__main__":
    sys.exit(main())
