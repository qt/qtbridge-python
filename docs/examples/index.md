# Examples

These runnable examples are included in the `examples/` directory of the
QtBridge source repository.  Each example has its own README with setup
instructions.

| Example | What it shows |
|---|---|
| [minimal_app](minimal_app/README) | Bare-minimum `bridge_instance()` + QML list view |
| [counter](counter/README) | `bridge_type()` with auto-properties, signals, and `@watch` |
| [controls_from_python](controls_from_python/README) | QtQuick Controls created entirely from Python |
| [qml_component_loading](qml_component_loading/README) | Loading custom `.qml` components from Python |
| [iris](iris/README) | `polars.DataFrame` table model for `TableView` |
| [graph_lineseries](graph_lineseries/README) | Chart line-series driven by a Python model |
| [quiz_example](quiz_example/README) | `bridge_type()`, `@computed`, `@complete` |
| [user_dataset](user_dataset/README) | `list[dict]` multi-role model with filtering |
| [colorpaletteclient](colorpaletteclient/README) | Full-stack REST client: pagination, auth, CRUD |

---

```{toctree}
:maxdepth: 1

minimal_app/README
counter/README
controls_from_python/README
qml_component_loading/README
iris/README
graph_lineseries/README
quiz_example/README
user_dataset/README
colorpaletteclient/README
```
