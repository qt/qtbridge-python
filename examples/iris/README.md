# Iris Dataset CRUD — DuckDB + Polars + QtBridge

A port of the [PySide6 pandas DataFrame example](https://doc.qt.io/qtforpython-6/examples/example_external_pandas.html)
to **Qt Quick**, replacing pandas with **Polars** and adding full CRUD
support backed by an in-memory **DuckDB** database.

| Original (QtWidgets + pandas) | This example (Qt Quick + Polars + DuckDB) |
|---|---|
| `QTableView` | QML `TableView` + `HorizontalHeaderView` |
| `QAbstractTableModel` subclass | Plain Python class + QtBridge `bridge_instance` |
| Read-only | Insert, Edit, Delete via `@insert`, `@edit`, `@remove` |
| pandas `DataFrame` | polars `DataFrame` |
| — | DuckDB for SQL-based CRUD |

## Architecture

```
┌────────────┐     SQL      ┌──────────┐    .pl()     ┌────────┐   QAIM    ┌─────────────┐
│  iris.csv  │───▶│  DuckDB  │──────────▶│ Polars  │─────────▶│  QML Table  │
└────────────┘   (in-memory) └──────────┘ DataFrame  └────────┘  (TableView) └─────────────┘
                     ▲                                     │
                     │              QtBridge decorators     │
                     └── INSERT / UPDATE / DELETE ◀────────┘
                         (@insert / @edit / @remove)
```

1. On startup the CSV is loaded into an in-memory DuckDB table with a
   synthetic `id` column for stable row identity.
2. `data()` returns a `polars.DataFrame` (minus the `id` column) which
   QtBridge automatically maps to a `QAbstractItemModel`.
3. Mutations go through DuckDB SQL; after each one the Polars cache is
   refreshed and the appropriate Qt model signal is emitted.

## Why DuckDB?

- **In-process** — no server, no network; just an embedded analytical DB.
- **Native Polars integration** — `conn.execute(...).pl()` gives you a
  zero-copy Polars DataFrame via Apache Arrow.
- **SQL for CRUD** — familiar `INSERT`, `UPDATE`, `DELETE` semantics keep
  the data-management code clean and declarative.
- **Transactional** — each mutation is atomic; no partial state.

> **Note**
> The `iris.csv` file uses column names `sepal.length`, `sepal.width`, `petal.length`,
`petal.width`, and `variety`.DuckDB normalizes these to underscore names (`sepal_length`,
`sepal_width`, `petal_length`, `petal_width`, `variety`) on import.

## Prerequisites

```bash
pip install duckdb polars pyarrow
```
(QtBridge and PySide6 are assumed to be installed already.)

## Running

1. Run:

```bash
python main.py
```

## Usage

| Action | How |
|---|---|
| **View** | Data is displayed automatically on startup |
| **Select** | Click any row to select it (click again to deselect) |
| **Add** | Click **＋ Add** → fill in the fields → OK |
| **Edit** | Select a row → click **✎ Edit** → modify fields → OK |
| **Delete** | Select a row → click **✕ Delete** → confirm |

## Key QtBridge Concepts

- **`bridge_instance`** — exposes a single Python object as a QML
  singleton.  The `data() -> polars.DataFrame` return type tells QtBridge
  to create a multi-column `QAbstractItemModel`.
- **`@insert`** — wraps the method call with `beginInsertRows` /
  `endInsertRows`, so the `TableView` animates the new row in.
- **`@remove`** — wraps with `beginRemoveRows` / `endRemoveRows`.
- **`@edit`** — emits `dataChanged` for the edited row across all columns,
  so the `TableView` updates in place without a full model reset.

## Files

| File | Purpose |
|---|---|
| `main.py` | Python model with DuckDB + Polars + QtBridge |
| `Main.qml` | Qt Quick UI — table, toolbar, CRUD dialogs |
| `iris.csv` | Dataset (copy here yourself) |
| `README.md` | This file |
