# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from QtBridge import bridge_instance, insert, remove, edit, qtbridge


class StringModel:
    def __init__(self):
        self._items = ["Apple", "Banana", "Cherry"]

    @insert
    def add_string(self, value: str):
        if value in self._items:
            print(f"Duplicate found: {value}")
            return False
        self._items.append(value)
        return True

    @remove
    def delete_string(self, index: int):
        if 0 <= index < len(self._items):
            value = self._items.pop(index)
            print(f"Deleted item: {value}")
            return True
        return False

    @edit
    def set_item(self, index: int, value: str):
        if 0 <= index < len(self._items):
            self._items[index] = value
            print(f"Item at index {index} set to {value}")
            return True
        return False

    def data(self) -> list[str]:
        return self._items


@qtbridge(module="Main")
def main():
    string_model = StringModel()
    # QML requires type names to start with an uppercase letter
    bridge_instance(string_model, name="String_model")


if __name__ == "__main__":
    main()
