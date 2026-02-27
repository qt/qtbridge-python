# QML Component Loading Example

This example demonstrates how to load and use QML-defined types from Python
using composition instead of inheritance.

## How It Works

A `Person` type is defined in QML (`person.qml`) with properties (`name`,
`age`), a signal (`birthdayHappened`), and a function (`celebrateBirthday`).

The Python `Employee` class composes a `Person` instance via
`load_qml_component()`:

```python
from QtBridge import load_qml_component

Person = load_qml_component("person.qml")

class Employee:
    def __init__(self, name, age, department):
        self.person = Person.create(name=name, age=age)
        self.department = department
        self.person.birthdayHappened.connect(self.on_birthday)
```

## Running

```bash
cd examples/qml_component_loading
python main.py
```
