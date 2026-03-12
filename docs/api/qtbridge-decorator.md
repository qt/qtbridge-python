(qtbridge-api)=
# `@qtbridge` — Application Entry Point

The `@qtbridge` decorator turns a plain Python function into a fully wired-up
QML application.  It creates a `QGuiApplication`, initialises a
`QQmlApplicationEngine`, loads your QML content, and starts the event loop.

---

## Signature

```python
@qtbridge(
    module: str | None = None,
    type_name: str | None = None,
    qml_file: str | None = None,
    import_paths: list[str] | None = None,
)
def main(...) -> None: ...
```

You must provide exactly **one** of `qml_file` or `module` (and optionally
`type_name` with `module`).

### Parameters

`qml_file`
: Path to a `.qml` file.  Can be relative to the Python script's directory.

`module`
: QML module name to load.  Requires a `qmldir` file in an import path that
  declares the module.  Example: `"Main"`.

`type_name`
: Specific type to load from the `module`.  Defaults to `"Main"` when omitted.

`import_paths`
: Additional QML import directories, relative to the Python script.  The
  script's own directory is always added automatically.

---

## The window parameter convention

If `main()` does not accept a parameter, that is the typical use case when
you use Qt Bridge as a data bridge: register models and types so QML can
access them during load. If you declare a first parameter, Qt Bridge will
also call `main()` after loading the QML and will pass the root QML object
(Application Window) into that parameter; you can then use that object to
manipulate UI-based Quick Controls components from Python (create/parent visual
items, set properties, connect signals, etc.).

### Pre-load registration (always run before QML loads)

The pre-load registration step is where you should register singleton models
and types so they are available to QML when the module/file is loaded. This
is executed regardless of whether you also declare a `window` parameter.

```python
@qtbridge(module="Main")
def main():
    # register models/types here (pre-load)
    bridge_instance(FruitModel(), name="Fruits")

if __name__ == "__main__":
    main()
```

### Post-load `window` parameter — for interacting with the UI

If your `main()` declares one parameter, `@qtbridge` will additionally call
it after the engine has loaded the QML and will pass the root QML object as
a {ref}`QmlObject <qmlobject-api>` wrapper. This post load call is intended for UI-specific
work — adjusting window properties, parenting or creating visual
components (for example via {ref}`load_qml_component() <load-qml-component-api>`), and connecting to
signals on QML objects. Avoid registering models in this post-load callback;
do that in the pre-load step above so QML sees them during load.

```{note}
The parameter name ``window`` is used here for simplicity. You can call it
whatever you like.
```

```python
@qtbridge(qml_file="Main.qml")
def main(window):
    # UI interactions only — models should already be registered
    window.title = "My App"
    window.width = 1024

    slider = Slider.create()
    slider.parent = window.contentItem
    slider.valueChanged.connect(lambda: print(slider.value))

if __name__ == "__main__":
    main()
```

---

## Additional import paths

```python
@qtbridge(
    module="Main",
    import_paths=["../shared_qml", "components/"],
)
def main():
    bridge_instance(Model(), name="DataModel")
```

Paths are relative to the Python script's directory and resolved before
the engine starts.

---

## Keep-alive of returned objects

For compatibility with PySide6 < 6.11, any value returned from `main()` is
held in memory for the lifetime of the application.  Use this to prevent
Python-created QML objects from being garbage-collected:

```python
@qtbridge(qml_file="Main.qml")
def main(window):
    widget = MyWidget.create()
    widget.parent = window.contentItem
    return widget   # keep alive

if __name__ == "__main__":
    main()
```

---

## See also

- {doc}`bridge-instance` — registering singleton models.
- {doc}`bridge-type` — registering instantiable types.
- {doc}`qml-component-loading` — creating QML objects from Python.
