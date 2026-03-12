(bridge-instance-api)=
# `bridge_instance()`

Register a Python object as a **QML singleton**.  The object (and its data)
become accessible from every QML file that imports the matching URI.

---

## Signatures

```python
# Overload 1 — class instance with a data() method
bridge_instance(
    instance: DataProvider,
    name: str,
    uri: str = "backend",
    auto_properties: bool = True,
    exclude_properties: set[str] | None = None,
) -> None

# Overload 2 — plain container (list / tuple / numpy.ndarray)
bridge_instance(
    obj: Any,
    name: str,
    uri: str = "backend",
    auto_properties: bool = True,
    exclude_properties: set[str] | None = None,
) -> None
```

### Parameters

`name`
: QML type name used to access the singleton.  **Must start with an uppercase
  letter** (QML naming requirement).

`uri`
: The QML import URI.  Defaults to `"backend"`.  In QML: `import backend 1.0`.

`auto_properties`
: When `True` (default), plain `self.x = …` assignments in `__init__` are
  automatically promoted to QML-visible properties with change-notification
  signals.  See {doc}`auto-properties` for details.


`exclude_properties`
: Set of attribute names to skip during auto-property generation.

---

## Supported data types

Qt Bridge detects the return type of `data()` and selects the appropriate
QML model automatically.

| Python type returned by `data()` | QML model behaviour | Available roles | Example use-case |
|---|---|---|---|
| `list[str]` / `list[int]` / `list[float]` | Single-role list | `display` | Simple string lists, number sequences |
| `list[dict]` | Multi-role table | Dict keys become role names | JSON API responses, database rows |
| `list[DataClass]` | Multi-role table | Dataclass fields become role names | Typed records |
| `polars.DataFrame` | Multi-role table | Column names become role names | Analytics, CSV/SQL data |
| `list` / `tuple` / `numpy.ndarray` *(no `data()` method)* | Single-role list | `display` | Quick prototypes |

### Single-role models

Suitable for `ListView`, `ComboBox`, `Repeater`:

```python
class FruitModel:
    def data(self) -> list[str]:
        return ["Apple", "Banana", "Cherry"]

bridge_instance(FruitModel(), name="Fruits")
```

```qml
ListView {
    model: Fruits
    delegate: Text { text: display }
}
```

### Multi-role models — `list[dict]`

Every key in the dict dictionaries becomes a named role.  All rows must share
the same set of keys.

```python
import json

class UserModel:
    def __init__(self):
        with open("users.json") as f:
            self._rows = json.load(f)   # list of {"name": …, "age": …, …}

    def data(self) -> list[dict]:
        return self._rows

bridge_instance(UserModel(), name="Users")
```

```qml
TableView {
    model: Users
    delegate: Text { text: name + " (" + age + ")" }
}
```

### Multi-role models — `list[DataClass]`

Dataclass fields become roles, with full type safety:

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    department: str

class UserModel:
    def __init__(self):
        self._users = [
            User("Alice", 30, "Engineering"),
            User("Bob", 25, "Design"),
        ]

    def data(self) -> list[User]:
        return self._users

bridge_instance(UserModel(), name="Users")
```

### Multi-role models — `polars.DataFrame`

Install polars with `pip install ".[table]"`:

```python
import polars as pl

class IrisModel:
    def __init__(self):
        self._df = pl.read_csv("iris.csv")

    def data(self) -> pl.DataFrame:
        return self._df

bridge_instance(IrisModel(), name="Iris")
```

Each column name becomes a role — access them directly in QML:

```qml
TableView {
    model: Iris
    delegate: Text { text: sepal_length }
}
```

### Plain containers (no `data()` method)

Wrap a raw list or array for a quick read-only singleton:

```python
bridge_instance([1, 2, 3, 4, 5], name="Numbers")
```

---

## Auto-properties

Any attribute set on `self` in `__init__` is automatically exposed to QML as a
readable/writable property with a change-notification signal (`xChanged`).

```python
class Settings:
    def __init__(self):
        self.theme = "dark"       # → Settings.theme (QML property)
        self.font_size = 14       # → Settings.fontSize (QML property)
        self._private = 0         # NOT exposed (underscore prefix)

bridge_instance(Settings(), name="AppSettings")
```

```qml
Text {
    text: AppSettings.theme   // reactive — updates when Python changes it
}
```

See {doc}`auto-properties` for the full rules.

---

## Combining data() with auto-properties

The two mechanisms work together.  The `data()` method provides the list/table
model; auto-properties expose scalar state (pagination, filters, loading flags):

```python
class UserModel:
    def __init__(self):
        self.is_loading = False
        self.current_page = 1
        self._rows: list[dict] = []

    def data(self) -> list[dict]:
        return self._rows

    @reset
    def fetch_page(self, page: int):
        self.is_loading = True
        self._rows = http_get(f"/users?page={page}")
        self.current_page = page
        self.is_loading = False

bridge_instance(UserModel(), name="Users")
```

---

## See also

- {doc}`model-decorators` — add `@insert`, `@remove`, `@edit`, `@reset` to make
  the model mutable from QML.
- {doc}`auto-properties` — detailed property generation rules.
- {doc}`../examples/index` — `minimal_app`, `user_dataset`, `iris` examples.
