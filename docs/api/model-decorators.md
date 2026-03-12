# Model Decorators

When a Python class is registered as a QML model via
{ref}`bridge_instance() <bridge-instance-api>` or
{ref}`bridge_type() <bridge-type-api>`, Qt requires the model to notify the
view about any data changes through the `QAbstractItemModel` protocol
(`beginInsertRows()` / `endInsertRows()`, etc.).

Qt Bridge handles all of that automatically via these decorators. Just
annotate the method and implement your data manipulation logic:

| Decorator | Qt notification | Use when |
|---|---|---|
| `@insert` | `beginInsertRows` / `endInsertRows` | Adding a row |
| `@remove` | `beginRemoveRows` / `endRemoveRows` | Deleting a row |
| `@edit` | `dataChanged` | Updating a cell/row in-place |
| `@move` | `beginMoveRows` / `endMoveRows` | Reordering rows |
| `@reset` | `beginResetModel` / `endResetModel` | Replacing all data |
| `@complete` | *(component lifecycle)* | Post-construction initialisation |

---

## `@insert`

```python
from QtBridge import insert

@insert
def add_item(self, value: str, index: int = -1) -> bool:
    if index == -1:
        self._items.append(value)
    else:
        self._items.insert(index, value)
    return True
```

- Pass `index` as a keyword argument to insert at a specific position;
  omit it (or use `-1`) to append.
- Return `False` to signal failure to the caller (no model notification is
  sent in that case).

```qml
Button { onClicked: Model.add_item("New item") }             // append
Button { onClicked: Model.add_item("First", index=0) }      // prepend
```

---

## `@remove`

```python
from QtBridge import remove

@remove
def delete_item(self, index: int) -> bool:
    if 0 <= index < len(self._items):
        self._items.pop(index)
        return True
    return False
```

```qml
Button { onClicked: Model.delete_item(index) }
```

---

## `@edit`

```python
from QtBridge import edit

@edit
def update_item(self, index: int, value: str) -> bool:
    if 0 <= index < len(self._items):
        self._items[index] = value
        return True
    return False
```

Qt Bridge calls `dataChanged()` for the row at `index` automatically.

```qml
TextField {
    onEditingFinished: Model.update_item(currentIndex, text)
}
```

---

## `@move`

```python
from QtBridge import move

@move
def reorder(self, from_index: int, to_index: int) -> bool:
    item = self._items.pop(from_index)
    self._items.insert(to_index, item)
    return True
```

```qml
// Drag-and-drop reorder
DragHandler { onActiveChanged: Model.reorder(dragIndex, dropIndex) }
```

---

## `@reset`

Use when the entire dataset changes (e.g. loading from a new API page,
switching database tables).

```python
from QtBridge import reset

@reset
def load_users(self, users: list[dict]) -> None:
    self._rows = users

@reset
def clear(self) -> None:
    self._rows = []
```

```qml
Button { onClicked: Model.load_users(fetchPage(2)) }
Button { onClicked: Model.clear() }
```

---

## `@complete` — Component lifecycle hook

`@complete` marks a method that QML calls automatically after a
{ref}`bridge_type() <bridge-type-api>`-registered component is
**fully constructed** i.e. after all property bindings declared in the
QML block have been applied.

It is analogous to `Component.onCompleted` in QML, but executes on the Python
side.

```python
from QtBridge import bridge_type, complete


class RestService:
    def __init__(self):
        self.url = ""            # set by QML before @complete fires
        self._client = None

    @complete
    def componentComplete(self):
        """Called after QML sets self.url via bindings."""
        print(f"Connecting to {self.url}")
        self._client = HttpClient(self.url)

    def data(self) -> list[dict]:
        return self._client.get("/items") if self._client else []


bridge_type(RestService, uri="backend", version="1.0")
```

```qml
import backend 1.0

RestService {
    url: "https://api.example.com"
    // componentComplete() fires here, after url is bound
}
```

### Important notes

- **Only for {ref}`bridge_type() <bridge-type-api>`** — `@complete` has no effect on
{ref}`bridge_instance() <bridge-instance-api>`.
- **Do not call it manually** — QML calls it at the right time.
- **Properties are ready** — all QML-declared property values are available
  inside the callback.
- **Analogous to** `QQmlParserStatus::componentComplete()` in C++.

---

## Combined example — mutable string list

```python
from QtBridge import bridge_instance, insert, remove, edit, qtbridge


class StringModel:
    def __init__(self):
        self._items = ["Apple", "Banana", "Cherry"]

    @insert
    def add_string(self, value: str) -> bool:
        if value in self._items:
            return False   # duplicate — no notification sent
        self._items.append(value)
        return True

    @remove
    def delete_string(self, index: int) -> bool:
        if 0 <= index < len(self._items):
            self._items.pop(index)
            return True
        return False

    @edit
    def set_item(self, index: int, value: str) -> bool:
        if 0 <= index < len(self._items):
            self._items[index] = value
            return True
        return False

    def data(self) -> list[str]:
        return self._items


@qtbridge(module="Main")
def main():
    bridge_instance(StringModel(), name="String_model")
```

---

## See also

- {doc}`bridge-instance` — registering singleton models.
- {doc}`bridge-type` — registering instantiable types.
- {doc}`../examples/index` — `minimal_app`, `iris`, `colorpaletteclient`.
