# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from QtBridge import bridge_instance, qtbridge

from pathlib import Path
import json


class UserDataModel:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent
        file_path = base_dir / "user_data.txt"
        with open(file_path) as json_data:
            self._data = json.load(json_data)

    def data(self) -> list[dict]:
        return self._data


@qtbridge(module="Main")
def main():
    model = UserDataModel()
    bridge_instance(model, name="UserData")


if __name__ == "__main__":
    main()
