# User Data Set Example

This example demonstrates how to load randomly generated user data from a JSON-formatted `.txt` file
and display it in a `TableView`.

The data is loaded at runtime and contains nested JSON structures.

## Functionality

- Loads user data from a JSON file
- Exposes Python data to QML using QtBridge
- Populates a `TableModel` dynamically
- Supports nested JSON properties (e.g. contact details)

## Purpose

This example illustrates how to:

- Use JSON data as a runtime data source
- Use nested JSON data directly with `TableModel`

## Key Concepts

### 1. Registering the Python Data Model

The Python class loads JSON data and exposes it to QML using `qtbridge`.

```python
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
```

### 2. Using the Data Model in QML

In the QML file `Main.qml`:

```qml
import QtQuick
import QtQuick.Controls
import backend 1.0

TableModel {
    id: tableModel

    TableModelColumn { display: "username" }
    TableModelColumn { display: "name" }
    TableModelColumn { display: "age" }
    TableModelColumn { display: "profession" }
    TableModelColumn { display: "is_active" }
    TableModelColumn { display: "email" }
    TableModelColumn { display: "phone" }
    TableModelColumn { display: "address" }
}

Repeater {
    model: UserData

    Item {
        Component.onCompleted: {
            tableModel.appendRow({
                "username": model.username,
                "name": model.name,
                "age": model.age,
                "profession": model.profession,
                "is_active": model.is_active,
                "email": model.contact.email,
                "phone": model.contact.phone,
                "address": model.address
            })
        }
    }
}

// ... TableView to display user data ...


TableView {
    model: tableModel
    // Example delegate showing how the nested address object
    // is accessed and formatted in TableView
    delegate: Text {
        text: display.street + ", " + display.postal_code + "\n"
            + display.city + ", " + display.country
    }
}
```

Note that `display` is the value provided by `TableModelColumn` and is equivalent to `model.display`
inside the delegate.

### 3. JSON Data Structure

```json
[
  {
    "id": "c8d519a7-959e-4322-875d-d98a14399b39",
    "name": "Jane Brown",
    "age": 36,
    "profession": "Engineer",
    "is_active": true,
    "username": "jbrown0",
    "contact": {
      "email": "jbrown0@example.com",
      "phone": "+49-627-244436"
    },
    "address": {
      "city": "Zurich",
      "country": "Switzerland",
      "street": "39 Example Street",
      "postal_code": "31014"
    }
  }
]
```

## How to Run

```sh
python main.py
```

## Summary

This example shows how nested JSON data can be loaded from a file, exposed through Python, and
displayed in a QML `TableView`.
