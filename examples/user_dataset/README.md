# User Data Set Example

This example demonstrates two ways to load user data from a JSON file and display it in a
`TableView` with column headers, using QtBridge to expose Python data to QML.

Two variants are provided, each in its own subdirectory, sharing a single QML file:

| Variant | Directory | Python return type |
|---|---|---|
| Plain JSON | `json/` | `list[dict]` |
| Polars DataFrame | `polars/` | `polars.DataFrame` |

## Folder Structure

```
user_dataset/
├── user_data.json       # Shared data source (nested JSON)
├── json/
│   └── main.py          # list[dict] variant
├── polars/
│   └── main.py          # polars.DataFrame variant
└── UserData/
    ├── qmldir           # QML module declaration (module UserData)
    └── Main.qml         # Shared QML file used by both variants
```

## Functionality

- Loads user data from `user_data.json` at runtime
- Exposes the data to QML via `bridge_instance()` as a `QAbstractItemModel` (QAIM)
- Displays all columns in a `TableView` with a `HorizontalHeaderView` for column names
- Column names are sourced automatically from the model via Qt's `DisplayRole` in `headerData()`

## Key Concepts

### 1. JSON Variant — `json/main.py`

The JSON variant manually flattens the nested JSON structure into a plain `list[dict]` with
scalar values only, since QML cannot render nested dicts as cell text directly.

```python
from QtBridge import bridge_instance, qtbridge
from pathlib import Path
import json

class UserDataModel:
    def __init__(self):
        file_path = Path(__file__).resolve().parent.parent / "user_data.json"
        with open(file_path) as f:
            raw = json.load(f)
        self._data = [
            {
                "username": user["username"],
                "name": user["name"],
                "age": user["age"],
                "profession": user["profession"],
                "is_active": user["is_active"],
                "email": user["contact"]["email"],
                "phone": user["contact"]["phone"],
                "city": user["address"]["city"],
                "country": user["address"]["country"],
                "street": user["address"]["street"],
                "postal_code": user["address"]["postal_code"],
            }
            for user in raw
        ]

    def data(self) -> list[dict]:
        return self._data

@qtbridge(module="UserData", type_name="Main", import_paths=[".."])
def main():
    model = UserDataModel()
    bridge_instance(model, name="UserData")
```

QtBridge detects the `list[dict]` return type and automatically builds a multi-column QAIM
where each dict key becomes a named role and a column. Column names are provided via
`headerData()` and read by `HorizontalHeaderView` using Qt's `DisplayRole`.

### 2. Polars Variant — `polars/main.py`

The Polars variant uses `pl.json_normalize()` to load and automatically flatten the nested JSON
into a `polars.DataFrame`. Nested fields receive dot-separated column names (e.g.
`contact.email`, `address.city`).

```python
from QtBridge import bridge_instance, qtbridge
from pathlib import Path
import json
import polars as pl

class UserDataModel:
    def __init__(self) -> None:
        file_path = Path(__file__).resolve().parent.parent / "user_data.json"
        with open(file_path) as f:
            self._data = pl.json_normalize(json.load(f))

    def data(self) -> pl.DataFrame:
        return self._data

@qtbridge(module="UserData", type_name="Main", import_paths=[".."])
def main():
    model = UserDataModel()
    bridge_instance(model, name="UserData")
```

QtBridge detects the `polars.DataFrame` return type and maps each column to a named role.
DataFrame column names (including dot-separated ones from `json_normalize`) are exposed via
`headerData()` and displayed automatically by `HorizontalHeaderView`.

### 3. Shared QML — `UserData/Main.qml`

Both variants use the same `UserData/Main.qml`. The QML file binds directly to the QAIM
provided by QtBridge — no `TableModel` or `Repeater` needed.

```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import backend 1.0

ApplicationWindow {
    ColumnLayout {
        // HorizontalHeaderView reads column names from headerData() via Qt::DisplayRole
        HorizontalHeaderView {
            id: horizontalHeader
            syncView: tableView

            delegate: Rectangle {
                // `display` is populated from headerData(section, Qt::Horizontal, Qt::DisplayRole)
                Text { text: display; font.bold: true }
            }
        }

        TableView {
            id: tableView
            model: UserData   // bound directly to the QtBridge QAIM

            delegate: Rectangle {
                Text {
                    text: {
                        if (column === 4)   // is_active column: render as Active / Inactive
                            return display ? "Active" : "Inactive"
                        return display !== undefined ? display : ""
                    }
                }
            }
        }
    }
}
```

The `display` property in the `HorizontalHeaderView` delegate is sourced from Qt's `DisplayRole`
via `headerData(section, Qt::Horizontal, Qt::DisplayRole)`. QtBridge populates this automatically
with the column name — the dict key for `list[dict]`, or the DataFrame column name for
`polars.DataFrame` (e.g. `contact.email` when using `json_normalize`).

In the `TableView` delegate, `display` is the cell value for the current row and column, also
sourced via `Qt::DisplayRole`.

### 4. QML Module and `import_paths`

The shared QML lives in `UserData/`, declared as the `UserData` QML module via `UserData/qmldir`.
Both `main.py` files specify `import_paths=[".."]` so Qt can locate `UserData/` relative to
each script's own directory, regardless of the working directory from which the example is launched.

```python
@qtbridge(module="UserData", type_name="Main", import_paths=[".."])
```

### 5. JSON Data Structure

```json
[
  {
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

**JSON variant:**

```sh
python json/main.py
```

**Polars variant** (requires `polars`; install with `pip install polars`):

```sh
python polars/main.py
```

Both can be run from any working directory — paths to `user_data.json` and the `UserData/`
QML module are resolved relative to each script's own location.

## Summary

This example shows two approaches to exposing tabular data to QML with QtBridge:

- **`list[dict]`** — simple and dependency-free; nested JSON must be flattened manually.
- **`polars.DataFrame`** — concise with `pl.json_normalize()`; handles nested JSON
  automatically, producing dot-separated column names.

Both variants share a single QML file that uses `HorizontalHeaderView` to display column names
sourced from the model's `headerData()` via `Qt::DisplayRole`, and `TableView` to render the
data rows — with no `TableModel` or `Repeater` required.
