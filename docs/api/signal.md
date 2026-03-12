# `Signal`

Qt Bridge provides its own `Signal` class that integrates seamlessly with the
Qt meta-object system.  Declare a class-level `Signal` to create custom
signals that can be connected and emitted across Python and QML.

---

## Declaration

```python
from QtBridge import Signal

class MyModel:
    valueChanged = Signal(int)         # carries one int argument
    ready = Signal()                   # no argument
    itemUpdated = Signal(str, int)     # two arguments
```
**Note:** Signals are class-level descriptors. Define them in the class body, not inside `__init__`.

---

## Emitting

Call `.emit()` on the bound instance:

```python
self.valueChanged.emit(42)
self.ready.emit()
self.itemUpdated.emit("Alice", 3)
```

---

## Connecting from Python

```python
model = MyModel()
model.valueChanged.connect(lambda v: print(f"value is {v}"))
model.ready.connect(on_ready_callback) # on_ready_callback is a Python method/function
```

---

## Connecting from QML

After registering the model with {ref}`bridge_instance() <bridge-instance-api>` or {ref}`bridge_type() <bridge-type-api>`, signals
appear automatically in QML:

```qml
Connections {
    target: MyModel
    function onValueChanged(v) { console.log("value:", v) }
    function onReady() { console.log("ready!") }
}
```

Or inline on QML instantiated types:

```qml
MyType {
    onValueChanged: (v) => console.log("value:", v)
}
```

---

## Disconnecting

```python
model.valueChanged.disconnect(my_slot)   # disconnect a specific slot
model.valueChanged.disconnect()           # disconnect all slots
```

---

## Auto-generated property signals

When {doc}`auto-properties` are enabled, Qt Bridge automatically creates a
`<name>Changed` signal for every auto-property.  You do **not** need to
declare these manually.

Additionally, Qt Bridge will also generate a `<name>Changed` signal for
explicit Python properties defined with the `@property` decorator when a
corresponding setter is provided. In other words, whether a property is
created via auto-property detection or implemented by a hand-written
`@property` with a setter, a `<name>Changed` signal will be available and
behaves the same.

```python
class Counter:
    def __init__(self):
        self.count = 0     # → countChanged signal generated automatically
```

```qml
Counter {
    onCountChanged: console.log("count is", count)
}
```

Explicitly declared `Signal` instances exist alongside auto-generated ones
and work identically.

---

## Full example

```python
from QtBridge import bridge_type, Signal, qtbridge


class DataLoader:
    loadStarted = Signal()
    loadFinished = Signal(int)   # number of rows loaded
    errorOccurred = Signal(str)

    def __init__(self):
        self._rows: list[dict] = []

    def load(self, url: str) -> None:
        self.loadStarted.emit()
        try:
            self._rows = fetch_data(url)
            self.loadFinished.emit(len(self._rows))
        except Exception as e:
            self.errorOccurred.emit(str(e))

    def data(self) -> list[dict]:
        return self._rows


bridge_type(DataLoader, uri="backend", version="1.0")
```

```qml
import backend 1.0

DataLoader {
    id: loader
    onLoadStarted:        busyIndicator.running = true
    onLoadFinished: (n) => { busyIndicator.running = false; statusLabel.text = n + " rows" }
    onErrorOccurred: (msg) => errorDialog.show(msg)
}

Button {
    text: "Load"
    onClicked: loader.load("https://api.example.com/data")
}
```

---

## See also

- {doc}`auto-properties` — automatically generated `<name>Changed` signals.
- {doc}`property-observers` — `@watch` / `@effect` for reacting to property
  changes on the Python side.
