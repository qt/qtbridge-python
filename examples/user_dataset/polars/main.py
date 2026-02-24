# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
Polars variant of the user_dataset example.

Reads user_data.json and returns a polars.DataFrame from data(). QtBridge
exposes this as a DataFrame QAIM (multi-column table), which Main.qml
consumes via model: UserData and HorizontalHeaderView.
"""

import json
import polars as pl

from pathlib import Path

from QtBridge import bridge_instance, qtbridge


class UserDataModel:
    def __init__(self) -> None:
        file_path = Path(__file__).resolve().parent.parent / "user_data.json"
        with open(file_path) as f:
            self._data = pl.json_normalize(json.load(f))

    def data(self) -> pl.DataFrame:
        return self._data


@qtbridge(module="UserData", type_name="Main", import_paths=[".."])
def main():
    model = UserDataModel()
    bridge_instance(model, name="UserData")


if __name__ == "__main__":
    main()
