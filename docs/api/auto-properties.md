# Auto-Properties

Qt Bridge can automatically convert plain Python instance attributes into
**QML-visible properties** with change notification signals.  Enable this
feature (the default) by passing `auto_properties=True` (the default) to
{ref}`bridge_instance() <bridge-instance-api>` or {ref}`bridge_type() <bridge-type-api>`.

---

## How it works

When Qt Bridge processes your class, it inspects the `__init__` method using
Python's `ast` module to find every `self.<name> = <value>` assignment.  For
each discovered attribute it:

1. Creates a QML-readable/writable property backed by a Python descriptor.
2. Generates a `<name>Changed` signal (e.g. `count` → `countChanged`).
3. Emits that signal whenever the value changes.

This all happens at registration time i.e. before any instances are created.

---

## Rules

### What gets promoted

```python
class Model:
    def __init__(self):
        self.count = 0          # ✓ plain assignment → QML property
        self.label: str = ""    # ✓ annotated assignment → QML property
        self._internal = 0      # ✗ underscore prefix → skipped
        self.__private = 0      # ✗ dunder prefix → skipped
```

Properties defined with `@property` decorators are **never** overridden by
auto-property generation.  If you need custom getter/setter logic, just write a
`@property`. That takes precedence.

### Underscore convention

Attributes whose names start with `_` are treated as implementation details
and are not exposed to QML.  Use this to keep internal state private:

```python
class PaginatedModel:
    def __init__(self):
        self.current_page = 1    # exposed
        self._cache: list = []   # internal — not exposed
```

### `exclude_properties`

Fine-grained control: pass a set of names to skip even without a leading `_`:

```python
bridge_instance(model, name="Config",
                exclude_properties={"debug_token", "api_key"})
```

---

## Signal naming

The generated signal is `<attributeName>Changed` (camelCase):

| Attribute | Signal |
|---|---|
| `count` | `countChanged` |
| `font_size` | `font_sizeChanged` |
| `isEnabled` | `isEnabledChanged` |

---

## First-write behaviour

The very first assignment in `__init__` initialises the value silently — no
signal is emitted and no `@watch` / `@effect` observers fire.  All subsequent
writes trigger the normal signal+observer chain.

---

## Reading and writing from QML

```python
class Settings:
    def __init__(self):
        self.theme = "dark"
        self.font_size = 14

bridge_instance(Settings(), name="AppSettings")
```

```qml
// Read
Text { text: AppSettings.theme }

// Write (from QML, triggers Python setter → signal emission)
Switch {
    onCheckedChanged: AppSettings.theme = checked ? "light" : "dark"
}

// Binding (reactive)
Text {
    font.pixelSize: AppSettings.font_size
}
```

---

## Updating from Python

Assign to `self.attr` normally inside any method:

```python
def toggle_theme(self):
    self.theme = "light" if self.theme == "dark" else "dark"
    # ↑ emits themeChanged → QML bindings update automatically
```

---

## Opting out

Pass `auto_properties=False` to manage QML properties entirely yourself
using PySide6's `@Property` / `Signal` APIs:

```python
bridge_type(MyType, auto_properties=False)
```


---

## See also

- {doc}`property-observers` — `@watch` and `@effect` for reacting to changes
  in Python.
- {doc}`signal` — declaring explicit signals.
- {doc}`bridge-instance` / {doc}`bridge-type` — where `auto_properties` is set.
