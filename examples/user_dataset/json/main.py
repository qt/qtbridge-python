# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from QtBridge import bridge_instance, qtbridge

from pathlib import Path
import json


class UserDataModel:
    def __init__(self):
        file_path = Path(__file__).resolve().parent.parent / "user_data.json"
        with open(file_path) as f:
            raw = json.load(f)
        self._data = [
            {
                "username": user["username"],
                "name": user["name"],
                "age": user["age"],
                "profession": user["profession"],
                "is_active": user["is_active"],
                "email": user["contact"]["email"],
                "phone": user["contact"]["phone"],
                "city": user["address"]["city"],
                "country": user["address"]["country"],
                "street": user["address"]["street"],
                "postal_code": user["address"]["postal_code"],
            }
            for user in raw
        ]

    def data(self) -> list[dict]:
        return self._data


@qtbridge(module="UserData", type_name="Main", import_paths=[".."])
def main():
    model = UserDataModel()
    bridge_instance(model, name="UserData")


if __name__ == "__main__":
    main()
