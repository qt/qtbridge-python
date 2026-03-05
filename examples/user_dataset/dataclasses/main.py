# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
Dataclass variant of the user_dataset example.

Reads user_data.json, populates a list of UserRecord dataclasses and passes
it to QtBridge as the data() return value.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from QtBridge import bridge_instance, qtbridge


@dataclass
class UserRecord:
    username: str
    name: str
    age: int
    profession: str
    is_active: bool
    email: str
    phone: str
    city: str
    country: str
    street: str
    postal_code: str


class UserDataModel:
    def __init__(self) -> None:
        file_path = Path(__file__).resolve().parent.parent / "user_data.json"
        with open(file_path) as f:
            raw = json.load(f)
        self._data = [
            UserRecord(
                username=user["username"],
                name=user["name"],
                age=user["age"],
                profession=user["profession"],
                is_active=user["is_active"],
                email=user["contact"]["email"],
                phone=user["contact"]["phone"],
                city=user["address"]["city"],
                country=user["address"]["country"],
                street=user["address"]["street"],
                postal_code=user["address"]["postal_code"],
            )
            for user in raw
        ]

    def data(self) -> list[UserRecord]:
        return self._data


@qtbridge(module="UserData", type_name="Main", import_paths=[".."])
def main():
    model = UserDataModel()
    bridge_instance(model, name="UserData")


if __name__ == "__main__":
    sys.exit(main())
