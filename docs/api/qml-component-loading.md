# QML Component Loading

Qt Bridge lets you **create and control QML objects entirely from Python**
including built-in QtQuick Controls (`Slider`, `Label`, `Button`, …) and
your own custom `.qml` components.

This makes it possible to build UIs and react to their events without
writing any QML yourself.

---

(load-qml-component-api)=
## `load_qml_component()`

```python
# From a .qml file
Factory = load_qml_component("path/to/Component.qml")

# From a QML module
Factory = load_qml_component(module="QtQuick.Controls", type_name="Slider")
```

Returns a `QmlComponentFactory`.  The factory is lightweight. The actual QML
loading and object creation is lazy and deferred to `.create()`, which requires
the `@qtbridge` engine to be running.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `source` | `str` | Path to a `.qml` file (absolute or relative to caller's directory) |
| `module` | `str` | QML module URI, e.g. `"QtQuick.Controls"` |
| `type_name` | `str` | Type name within the module, e.g. `"Slider"` |

Exactly one of `source` or (`module` + `type_name`) must be supplied.

---

## `QmlComponentFactory.create()`

```python
obj = Factory.create(**initial_properties)
```

Instantiates the component and returns a `QmlObject` wrapper.

```python
Slider = load_qml_component(module="QtQuick.Controls", type_name="Slider")

@qtbridge(qml_file="Main.qml")
def main(window):
    slider = Slider.create()          # no initial properties
    slider.parent = window.contentItem
    slider.x = 20
    slider.y = 80
    slider.width = 300
    slider.stepSize = 0.05
```

Or set initial properties in one call:

```python
label = Label.create(text="Hello", x=20, y=20)
label.parent = window.contentItem
```

---

(qmlobject-api)=
## `QmlObject` — the returned wrapper

`QmlObject` wraps the underlying `QObject` and provides Pythonic access to
QML properties, signals, and methods.

### Reading and writing properties

```python
print(slider.value)       # read
slider.value = 0.5        # write (triggers QML binding updates)
slider.width = 400
```

### Connecting to signals

```python
def on_changed():
    print(f"slider value: {slider.value:.2f}")

slider.valueChanged.connect(on_changed)
```

### Calling QML methods

```python
result = myComponent.someMethod(arg1, arg2)
```

### Accessing the raw `QObject`

```python
raw_qobj = slider.qobject   # PySide6 QObject
```

### Nesting QML objects

Assign a `QmlObject` to a QML property that expects a `QObject`/`Item` as
the parent:

```python
child = Rectangle.create()
child.parent = window.contentItem   # QmlObject assigned via parent property
```

---

## Pattern 1 — Controls from Python

The {doc}`controls_from_python </examples/controls_from_python/README>` example
creates all UI controls without writing any QML component definitions.

```python
from PySide6.QtCore import QTimer
from QtBridge import load_qml_component, qtbridge

Slider = load_qml_component(module="QtQuick.Controls", type_name="Slider")
Label  = load_qml_component(module="QtQuick.Controls", type_name="Label")
Button = load_qml_component(module="QtQuick.Controls", type_name="Button")

@qtbridge(qml_file="Main.qml")
def main(window):
    content = window.contentItem
    win_w   = window.width

    heading = Label.create(text="Qt Controls — driven from Python")
    heading.parent = content
    heading.x, heading.y = 20, 20

    slider = Slider.create()
    slider.parent = content
    slider.x, slider.y = 20, 70
    slider.width = win_w - 40
    slider.stepSize = 0.01

    value_label = Label.create(text="Value: 0.00")
    value_label.parent = content
    value_label.x, value_label.y = 20, 130

    slider.valueChanged.connect(
        lambda: setattr(value_label, "text", f"Value: {slider.value:.2f}")
    )

    reset_btn = Button.create(text="Reset")
    reset_btn.parent = content
    reset_btn.x, reset_btn.y = 20, 180
    reset_btn.clicked.connect(lambda: setattr(slider, "value", 0.0))

    # Animate slider with a QTimer
    timer = QTimer()
    timer.timeout.connect(lambda: setattr(slider, "value",
                           (slider.value + 0.01) % 1.0))
    timer.start(50)
    return slider, value_label, reset_btn, timer   # keep alive
```

---

## Pattern 2 — Composing custom QML types

```python
# person.qml defines a Person component with name, age, and a
# birthdayHappened() signal declared in QML.

from QtBridge import load_qml_component, bridge_instance, qtbridge

Person = load_qml_component("person.qml")


class Employee:
    def __init__(self, name: str, age: int, department: str):
        self.person = Person.create(name=name, age=age)
        self.department = department
        self.person.birthdayHappened.connect(self._on_birthday)

    def _on_birthday(self):
        print(f"{self.person.name} is now {self.person.age}!")


@qtbridge(module="Main")
def main():
    emp = Employee("Alice", 28, "Engineering")
    bridge_instance(emp, name="CurrentEmployee")
    return emp.person   # keep alive
```

---

## Availability note

`load_qml_component()` requires the {ref}`@qtbridge <qtbridge-api>` engine to be initialised before
`factory.create()` is called.  The factory itself (`load_qml_component(…)`) can
be created at module level. The creation of the actual QML object must happen
inside `main()` or any code that runs after {ref}`@qtbridge <qtbridge-api>` starts the engine.

---

## See also

- {doc}`qtbridge-decorator` — the `@qtbridge` decorator that starts the engine.
- {doc}`../examples/index` — `controls_from_python`, `qml_component_loading` examples.
