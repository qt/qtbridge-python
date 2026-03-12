(bridge-type-api)=
# `bridge_type()`

Register a Python class as an **instantiable QML type**.  Unlike
{ref}`bridge_instance() <bridge-instance-api>`, which registers a single Python
object as a singleton, `bridge_type()` lets QML create multiple independent
instances of the class just like any built-in QML component.

---

## Signature

```python
bridge_type(
    type: type,
    uri: str | None = None,
    version: str | None = None,
    name: str | None = None,
    default_property: str | None = None,
    auto_properties: bool = True,
    exclude_properties: set[str] | None = None,
) -> None
```

### Parameters

`type`
: The Python class to register.

`uri`
: QML module URI.  Defaults to `"backend"`.

`version`
: Version string in `"major.minor"` format.  Defaults to `"1.0"`.

`name`
: QML type name.  Defaults to the Python class name.

`default_property`
: The property that receives children assigned in QML without an explicit
  property name (see the [Default property](#default-property) section).

`auto_properties`
: Automatically promote `self.x = …` assignments in `__init__` to QML
  properties.  Defaults to `True`.  See {doc}`auto-properties`.

`exclude_properties`
: Set of attribute names to exclude from auto-property generation.

---

## When to use `bridge_type` vs `bridge_instance`

| | `bridge_instance` | `bridge_type` |
|---|---|---|
| Number of objects | One singleton | Multiple, QML-created instances |
| Lifecycle control | Python controls lifetime | QML controls lifetime |
| `@complete` lifecycle hook | ✗ | ✓ |
| Use in QML | `ModelName.method()` | `MyType { … }` |

Use `bridge_type` when:

- QML needs to create several instances (e.g. a `Counter` per tab).
- The component's properties need to be set via QML property bindings.
- You want to react to component readiness with {doc}`model-decorators` (`@complete`).

---

## Basic example — Counter

```python
from QtBridge import bridge_type, qtbridge

class Counter:
    def __init__(self):
        self.count = 0       # auto-property → countChanged signal

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

bridge_type(Counter, uri="backend", version="1.0")
```

```qml
import backend 1.0

Counter {
    id: counter
    onCountChanged: console.log("count is now", count)
}

Button {
    text: "+"
    onClicked: counter.increment()
}
```

---

## Custom name and URI

```python
bridge_type(Counter, uri="myapp", version="2.0", name="MyCounter")
```

```qml
import myapp 2.0
MyCounter { id: c }
```

---

## Excluding auto-properties

Use `exclude_properties` to keep internal attributes hidden from QML:

```python
class Config:
    def __init__(self):
        self.host = "localhost"
        self.port = 8080
        self.debug_token = "secret"   # should NOT be in QML

bridge_type(Config, exclude_properties={"debug_token"})
```

---

(default-property)=
## Default property

The `default_property` parameter designates which property receives child
items assigned inside a QML block, mirroring Qt's `DefaultProperty` concept.

```python
from QtBridge import bridge_type

class Box:
    def __init__(self):
        self._items: list = []

    @property
    def items(self) -> list:
        return self._items

    @items.setter
    def items(self, value):
        self._items = value

bridge_type(Box, uri="myapp", version="1.0", default_property="items")
```

```qml
import myapp 1.0
import backend 1.0

Box {
    // These children are assigned to Box.items automatically:
    Counter {}
    Counter {}
}
```

---

## Lifecycle with `@complete`

For types registered with `bridge_type()`, the {doc}`model-decorators` section
covers the `@complete` decorator, a hook called by QML after all properties
have been set and the component is fully constructed:

```python
class RestService:
    def __init__(self):
        self.url = ""

    @complete
    def componentComplete(self):
        # Called AFTER QML sets self.url via bindings
        print(f"Connecting to {self.url}")
        self._client = HttpClient(self.url)
```

---

## See also

- {doc}`auto-properties` — how `self.x = 0` becomes a QML property.
- {doc}`model-decorators` — `@complete` and mutation decorators.
- {doc}`../examples/index` — `counter`, `colorpaletteclient` examples.
