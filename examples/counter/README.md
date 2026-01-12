# Counter Example

This example demonstrates a simple counter application with increment and decrement functionality,
using a Python backend and a QML frontend.

## Functionality

- Displays a count value in the center of the window
- Provides a `+` button to increment and a `−` button to decrement the count
- The count is stored and managed in a Python class, but can be accessed and modified directly from
  QML

## Purpose

This example shows how to use `bridge_type()` to register a Python class as a QML type, allowing you
to instantiate and use Python objects directly in QML.

## Key Concepts

### 1. Registering the Python Type

In the Python backend (`counter.py`):

```python
from QtBridge import qtbridge, bridge_type

class CounterModel:
    def __init__(self):
    self._count = 0
    # ... property and setter ...

@qtbridge(module="CounterModel")
def main():
	bridge_type(CounterModel, uri="backend", version="1.0")
```

The call to `bridge_type(CounterModel, uri="backend", version="1.0")` makes the `CounterModel`
Python class available as a QML type in the `backend` module (the default module name).

### 2. Using the Python Type in QML

In the QML file (e.g. `CounterModel.qml`):

```qml
import backend 1.0

ApplicationWindow {
	CounterModel {
		id: counterModel
		count: 5
	}
	// ... UI ...
}
```

You can now create and use `CounterModel` directly in QML, set its properties, and bind to them.

## How to Run

```sh
python counter.py
```

## Summary

This example is a minimal demonstration of how to expose Python logic to QML using `bridge_type()`,
 enabling seamless integration between Python and QML for rapid UI development.

