# String List Manager Example

This example demonstrates a simple string list manager with add, edit, and delete functionality,
using a Python backend and a QML frontend.

## Functionality

- Displays a list of strings in a scrollable view
- Provides a text field and button to add new strings
- Each list item can be edited inline by clicking on the text
- Each list item has a delete button (×) to remove it from the list
- The data is stored and managed in a Python class, exposed to QML as a singleton.

## Purpose

This example shows how to use `bridge_instance()` to expose a Python object instance to QML,
allowing you to use Python-managed data directly as a QML model.

## Key Concepts

### 1. Exposing a Python Instance to QML

In the Python backend (`main.py`):

```python
from QtBridge import bridge_instance, insert, remove, edit, qtbridge

class StringModel:
    def __init__(self):
        self._items = ["Apple", "Banana", "Cherry"]

    @insert
    def add_string(self, value: str):
        # Adds a new string to the list
        self._items.append(value)
        return True

    @remove
    def delete_string(self, index: int):
        # Removes a string at the specified index
        self._items.pop(index)
        return True

    @edit
    def set_item(self, index: int, value: str):
        # Updates a string at the specified index
        self._items[index] = value
        return True

    def data(self) -> list[str]:
        # Returns the list data for QML to display
        return self._items

@qtbridge(module="Main")
def main():
    string_model = StringModel()
    # Expose the Python instance to QML with the name "String_model"
    bridge_instance(string_model, name="String_model")
```

The `bridge_instance(string_model, name="String_model")` call makes the Python object available in
QML as `String_model`. This allows QML to:
- Use it directly as a model for ListView
- Call its methods (add_string, delete_string, set_item)
- Receive automatic updates when the data changes with the help of `@insert`, `@remove` and
  `@edit` decorators.

Note: When exposing a Python instance to QML, it is generally assumed that this instance
is used for manipulating and storing certain data. Hence, it is required by the user to implement
a `data` method which returns the actual data.

### 2. Using Decorators for Model Updates

The decorators `@insert`, `@remove`, and `@edit` automatically notify QML when the underlying
data changes:

- `@insert`: Notifies QML when items are added to the list
- `@remove`: Notifies QML when items are removed from the list
- `@edit`: Notifies QML when items are modified

This eliminates the need for manual signal emission (as opposed to PySide6) and keeps your Python
code clean.

### 3. Using the Python Instance in QML

In the QML file (`Main.qml`):

```qml
import backend 1.0

ApplicationWindow {
    ListView {
        model: String_model  // Direct reference to the Python instance
        delegate: Rectangle {
            required property int index
            required property string display

            TextField {
                text: display
                onEditingFinished: {
                    // Call Python method to update the item
                    String_model.set_item(index, text)
                }
            }

            Button {
                text: "×"
                onClicked: {
                    // Call Python method to delete the item
                    String_model.delete_string(index)
                }
            }
        }
    }

    TextField {
        id: input
        onAccepted: {
            // Call Python method to add a new item
            String_model.add_string(input.text)
            input.clear()
        }
    }
}
```

## Running the Example

```bash
python main.py
```
