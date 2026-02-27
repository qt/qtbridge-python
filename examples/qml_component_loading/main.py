# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
Demonstrates composition-based QML component loading from Python.

A QML-defined ``Person`` type is loaded and used inside a plain Python
``Employee`` class via composition.
"""

import sys
from QtBridge import qtbridge, bridge_instance, load_qml_component

Person = load_qml_component("person.qml")

class Employee:
    """Plain Python class that *composes* a QML Person object."""

    def __init__(self, name: str, age: int, department: str):
        # Create a QML Person instance; properties set via createWithInitialProperties
        self.person = Person.create(name=name, age=age)
        self.department = department

        # Connect to the QML signal from Python
        self.person.birthdayHappened.connect(self._on_birthday)

    def _on_birthday(self):
        print(f"{self.person.name} is now {self.person.age}!")

    def celebrate(self):
        self.person.celebrateBirthday()


@qtbridge(qml_file="Main.qml")
def main():
    emp = Employee("Alice", 28, "Engineering")
    emp.celebrate()  # → prints "Alice is now 29!"
    bridge_instance(emp, name="EmployeeModel")


if __name__ == "__main__":
    sys.exit(main())

