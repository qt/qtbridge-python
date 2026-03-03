# Controls from Python Example

This example demonstrates that `load_qml_component()` works not only with
non-visual `QtObject` types but also with real **QtQuick Controls** widgets.

## What it shows

All UI controls are **created and wired up entirely from Python** — `Main.qml`
provides only a bare `ApplicationWindow`.

| Widget | Created from |
|--------|-------------|
| `Label` (heading) | `load_qml_component(module="QtQuick.Controls", type_name="Label")` |
| `Slider` | `load_qml_component(module="QtQuick.Controls", type_name="Slider")` |
| `Label` (value) | updated from Python via `slider.qobject.valueChanged` signal |
| `Button` (Reset) | `load_qml_component(module="QtQuick.Controls", type_name="Button")` |
| `Label` (status) | updated by Python timer and button handler |

## How it works

1. `load_qml_component()` returns a `QmlComponentFactory`.
2. After `@qtbridge` starts the engine, `.create()` uses `QQmlComponent` to
   instantiate the control as a `QmlObject`.
3. The underlying `QQuickItem` is parented into the window's `contentItem`
   via `setProperty("parent", content)`.
4. Properties (`x`, `y`, `width`, `value`, `text`, …) are set directly on the
   `QmlObject` wrapper.
5. Signals (`valueChanged`, `clicked`) are connected to plain Python functions.
6. A `QTimer` drives the `Slider` forward automatically, showing Python fully
   in control of the widget state.

## Running

```bash
cd examples/controls_from_python
python main.py
```

You should see:
- A `Slider` that animates forward automatically (driven by a Python `QTimer`).
- A live **Value** label that updates as the slider moves.
- A **Reset** button that, when clicked, sets the slider back to 0 from Python.
