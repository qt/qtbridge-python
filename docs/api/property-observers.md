# Property Observers: `@watch` and `@effect`

Property observers let you react to {doc}`auto-property <auto-properties>`
changes entirely on the **Python side**. No QML connections required.

All observers fire **synchronously** from the property setter, immediately
after the new value has been stored and the `Changed` signal emitted.
They are not fired during the initial `__init__` assignment.

---

## `@watch` — observe a single property

```python
from QtBridge import watch, Change

@watch("property_name")
def method(self, change: Change) -> None:
    ...
```

The callback receives a `Change` object every time the named property changes.

### `Change` object

| Attribute | Type | Description |
|---|---|---|
| `change.name` | `str` | Name of the property that changed |
| `change.old` | `Any` | Value before the change |
| `change.new` | `Any` | Value after the change |
| `change.owner` | `Any` | The object instance |

### Example

```python
from QtBridge import bridge_type, watch, Change


class Counter:
    def __init__(self):
        self.count = 0

    @watch("count")
    def _log_change(self, change: Change) -> None:
        print(f"count: {change.old} → {change.new}")
```

### Stacking `@watch`

A single method can watch **multiple** properties by stacking the decorator:

```python
@watch("width")
@watch("height")
def _on_resize(self, change: Change) -> None:
    print(f"{change.name} changed: {change.old} → {change.new}")
```

---

## `@effect` — react to one or more properties

```python
from QtBridge import effect

@effect("prop1", "prop2", ...)
def method(self) -> None:
    ...
```

Called with no arguments whenever **any** of the listed properties change.
Ideal for side-effects such as derived computation, or logging where you do
not need the old value.

### Example

```python
from QtBridge import bridge_instance, effect


class Settings:
    def __init__(self):
        self.theme = "dark"
        self.font_size = 14

    @effect("theme", "font_size")
    def _persist(self) -> None:
        save_to_disk({"theme": self.theme, "font_size": self.font_size})


bridge_instance(Settings(), name="AppSettings")
```

### `@watch` vs `@effect`

| | `@watch` | `@effect` |
|---|---|---|
| Properties watched | One per decorator | Many, listed once |
| Arguments | `(self, change: Change)` | `(self)` |
| Gets old/new values | ✓ | ✗ |
| Best for | Logging, validation | Persistence, derived state |

---

<!--
## `@computed` — derived read-only properties  (not yet implemented)

A `@computed` property is a read-only auto-property whose value is derived from
other auto-properties.  Qt Bridge tracks the dependencies and re-evaluates
(and emits the change signal) whenever any dependency changes.

### Explicit dependencies

```python
from QtBridge import bridge_type
# @computed is imported from the same module
from QtBridge import computed   # if available in your build

class Cart:
    def __init__(self):
        self.price = 10.0
        self.quantity = 1

    @computed("price", "quantity")
    def total(self) -> float:
        return self.price * self.quantity
```

`total` is read-only — assigning to `self.total = …` raises `AttributeError`.
`totalChanged` is emitted automatically when `price` or `quantity` change.

### Auto-tracked dependencies

```python
class Profile:
    def __init__(self):
        self.first = "Ada"
        self.last = "Lovelace"

    @computed
    def full_name(self) -> str:
        # Qt Bridge discovers "first" and "last" as dependencies automatically
        return f"{self.first} {self.last}"
```

### `@computed` behaviour

- **Read-only**: setting raises `AttributeError`.
- **Cached**: value is only recomputed when at least one dependency changes.
- **Signal**: `<name>Changed` is emitted when the cached value changes.
- **Observable**: you can `@watch` a computed property just like a plain one.
-->


## Real-world pattern — counter with milestones

From the `counter` example:

```python
from QtBridge import bridge_type, qtbridge, watch, effect, Change


class CounterModel:
    def __init__(self):
        self.count = 0

    @watch("count")
    def _log_count_change(self, change: Change) -> None:
        print(f"[watch] count changed: {change.old} → {change.new}")

    @effect("count")
    def _check_milestone(self) -> None:
        milestones = {5: "High five! 🖐", 10: "Perfect ten! 🎯"}
        if self.count in milestones:
            print(f"[effect] {milestones[self.count]}")


@qtbridge(module="CounterModel")
def main():
    bridge_type(CounterModel, uri="backend", version="1.0")
```

---

## See also

- {doc}`auto-properties` — how the properties being observed are generated.
- {doc}`signal` — explicit `Signal` declarations.
- {doc}`../examples/index` — `counter` example demonstrates `@watch` and `@effect`.
