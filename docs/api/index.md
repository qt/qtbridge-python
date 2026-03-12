# API Reference

Qt Bridge exposes a small, focused public API.  Everything you need is
importable directly from `QtBridge`:

```python
from QtBridge import (
    bridge_instance,       # Register an instance as a QML singleton
    bridge_type,           # Register a class as an instantiable QML type
    qtbridge,              # Application entry-point decorator
    Signal,                # Declare custom signals
    insert, remove, edit,  # Model mutation decorators
    move, reset, complete, # Model mutation decorators (continued)
    watch, effect,         # Property observer decorators
    Change,                # Change descriptor passed to @watch callbacks
    load_qml_component,    # Load a QML component for use from Python
    QmlObject,             # Wrapper around a QML-created QObject
    QmlComponentFactory,   # Factory returned by load_qml_component()
)
```

## Choosing the right API

| Scenario | API |
|---|---|
| Expose a Python object as a **singleton** model | `bridge_instance()` |
| Register a Python class that QML can **instantiate** | `bridge_type()` |
| Run a QML application and wire up the bridge | `@qtbridge` |
| Declare a custom signal | `Signal` |
| React to model mutations from QML | `@insert`, `@remove`, `@edit`, `@move`, `@reset` |
| Run Python code once QML component is fully ready | `@complete` |
| Watch for property changes in Python | `@watch`, `@effect` |
| Create and control QML objects from Python | `load_qml_component()` |

---

```{toctree}
:maxdepth: 1

bridge-instance
bridge-type
qtbridge-decorator
signal
auto-properties
property-observers
model-decorators
qml-component-loading
auto_full_api
```
