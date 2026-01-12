# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

from typing import Any, List, Protocol, overload
from collections.abc import Callable


class DataProvider(Protocol):
    """
    Defines the required interface for data models.
    """
    def data(self) -> Any:
        """
        Returns the data structure to be exposed to QML.
        """
    ...

@overload
def bridge_instance(instance: DataProvider, name: str, uri: str = "backend") -> None:
    """
    Registers a Python class instance as a QML singleton bridge.

    Parameters
    ----------
    instance : DataProvider
        A Python class instance that implements a `data()` method returning
        the data structure to expose to QML. Any object with a `data()` method
        satisfies this requirement.
    name : str
        The QML model name (must start with an uppercase letter).
    uri : str, optional
        The QML module URI under which the singleton will be registered.
        Defaults to "backend".

    Example
    -------
    ```python
    from QtBridge import bridge_instance

    class StringModel:
        def __init__(self):
            self._items = ["Apple", "Banana", "Cherry"]

        def data(self) -> list[str]:
            return self._items

    model = StringModel()
    bridge_instance(model, name="String_model")
    ```

    In QML:
    ```qml
    import backend 1.0

    ListView {
        model: String_model
        delegate: Text { text: display }
    }
    ```
    """
    ...

@overload
def bridge_instance(obj: Any, name: str, uri: str = "backend") -> None:
    """
    Exposes Python containers (list, tuple, or numpy.ndarray) as a QML
    singleton instance.

    The container is wrapped in a `QRangeModel`, providing a model accessible
    from QML. This overload is useful for simple data structures that don't
    require a custom class implementation.

    Parameters
    ----------
    obj : Any
        The Python container to expose to QML. Supports list, tuple,, and
        numpy.ndarray (if numpy is installed). The container's
        elements will be accessible via the `display` role in QML.
    name : str
        The QML model name (must start with an uppercase letter).
    uri : str, optional
        The QML module URI under which the singleton will be registered.
        Defaults to "backend".

    Example
    -------
    ```python
    from QtBridge import bridge_instance

    # Simple list
    bridge_instance(["A", "B", "C"], name="MyList")

    # Numpy array (if numpy is installed)
    import numpy as np
    bridge_instance(np.array([1, 2, 3]), name="MyArray")
    ```

    In QML:
    ```qml
    import backend 1.0

    ListView {
        model: MyList
        delegate: Text { text: display }
    }
    ```
    """
    ...

def bridge_type(type: type, uri: str | None = None, version: str | None = None, name: str | None = None, default_property: str | None = None) -> None:
    """
    Registers a Python class as a QML type.

    Parameters
    ----------
    type : type
        The Python class type to register as a QML type.
    uri : str, optional
        The QML module name under which the type will be available.
    version : str, optional
        QML version in `"major.minor"` format, e.g. `"1.0"`.
    name : str, optional
        Custom name to use for the QML type. Defaults to the Python
        class name if not provided.
    default_property : str, optional
        The name of a property in the Python class to be treated as the
        default property in QML.
    """
    ...

def insert(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that marks a method as an *insert* operation for QML-bound
    list or table models.

    Methods decorated with `@insert` are automatically recognized
    by the Qt bridge as functions responsible for adding new elements
    to a model exposed to QML. The decorated method triggers
    `beginInsertRows()` and `endInsertRows()` of Qt automatically.

    Parameters
    ----------
    func : Callable
        The function that implements the insert behavior.

    Keyword Arguments (when calling the decorated method)
    -----------------------------------------------------
    index : int, optional
        The position at which to insert the item. If not provided,
        the item is appended to the end. When provided, inserts at
        the specified position.

    Example
    -------
    >>> @insert
    ... def add_item(self, name: str):
    ...     self._items.append(name)
    >>>
    >>> # From QML or Python:
    >>> model.add_item("test")  # Appends to end
    >>> model.add_item("test", index=0)  # Inserts at beginning
    """
    ...

def move(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that marks a method as a *move* operation for QML-bound
    models.

    Methods decorated with `@move` allow elements in a list or table to
    be rearranged from QML. The decorated method triggers
    `beginMoveRows()` and `endMoveRows()` of Qt automatically.

    Parameters
    ----------
    func : Callable
        The function implementing the move behavior.

    Keyword/Positional Arguments (when calling the decorated method)
    ----------------------------------------------------------------
    from_index : int
        The source position of the item to move (can be positional or keyword)
    to_index : int
        The destination position for the item (can be positional or keyword)

    Example
    -------
    >>> @move
    ... def move_item(self, from_idx: int, to_idx: int):
    ...     item = self._items.pop(from_idx)
    ...     self._items.insert(to_idx, item)
    >>>
    >>> # From QML or Python:
    >>> model.move_item(0, 3)  # Move from index 0 to 3
    >>> model.move_item(from_index=0, to_index=3)  # Same with keywords
    """
    ...

def edit(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that marks a method as an *edit* operation for QML-bound
    models.

    Methods decorated with `@edit` are recognized by the Qt bridge
    as update operations for modifying existing data in the model.
    The decorated method triggers `dataChanged()` of Qt automatically.

    Parameters
    ----------
    func : Callable
        The function implementing the edit logic.

    Keyword/Positional Arguments (when calling the decorated method)
    ----------------------------------------------------------------
    index : int
        The position of the item to edit (can be positional or keyword)
    *args : Any
        Additional arguments for the new values

    Example
    -------
    >>> @edit
    ... def update_item(self, idx: int, name: str):
    ...     self._items[idx] = name
    >>>
    >>> # From QML or Python:
    >>> model.update_item(0, "new name")  # Positional
    >>> model.update_item(index=0, name="new name")  # Keywords
    """
    ...

def remove(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that marks a method as a *remove* operation for QML-bound
    list or table models.

    Methods decorated with `@remove` are exposed to QML as callable
    slots that handle item removal. The decorated method triggers
    `beginRemoveRows()` and `endRemoveRows()` of Qt automatically.

    Parameters
    ----------
    func : Callable
        The function that removes an element from the model.

    Keyword/Positional Arguments (when calling the decorated method)
    ----------------------------------------------------------------
    index : int
        The position of the item to remove (can be positional or keyword)

    Example
    -------
    >>> @remove
    ... def delete_item(self, idx: int):
    ...     del self._items[idx]
    >>>
    >>> # From QML or Python:
    >>> model.delete_item(0)  # Positional
    >>> model.delete_item(index=2)  # Keyword
    """
    ...

def qtbridge(module: str | None = None, type_name: str | None = None, qml_file: str | None = None, import_paths: List[str] | None = None) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """
    Decorator that abstracts the calling of qml file/module.

    The `@qtbridge` decorator transforms a normal Python function into an entry
    point for a QML-based application. It initializes the `QGuiApplication`,
    creates a `QQmlApplicationEngine`, loads the QML file/module, and starts
    the Qt event loop.

    Parameters
    ----------
    module : str, optional
        The name of a QML module to load (e.g. `"Main"`).
        Example: `engine.loadFromModule("Main", "Window")`

    type_name : str, optional
        Specific QML type to load from the given module.

    qml_file : str, optional
        Path to a QML file (absolute or relative).

    import_paths : list[str], optional
        Additional import paths for QML modules.

    Example
    -------
    ```python
    from QtBridge import qtbridge, bridge_instance

    @qtbridge(module="Main")
    def main():
        data = ["Apple", "Banana", "Cherry"]
        bridge_instance(data, name="FruitModel")

    if __name__ == "__main__":
        main()
    ```
    """
    ...

def reset(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that marks a method as a *reset* operation for QML-bound
    models.

    Methods decorated with `@reset` are used to refresh or completely
    reload the data in the model from QML. The decorated method triggers
    `beginResetModel()` and `endResetModel()` of Qt automatically.

    Use this when the entire model contents need to be replaced, such as
    loading new data from a database or API.

    Parameters
    ----------
    func : Callable
        The function implementing the reset logic. May accept parameters
        for the new data.

    Example
    -------
    >>> @reset
    ... def load_data(self, new_items: list):
    ...     self._items = new_items.copy()
    >>>
    >>> @reset
    ... def clear_all(self):
    ...     self._items = []
    >>>
    >>> # From QML or Python:
    >>> model.load_data([1, 2, 3])
    >>> model.clear_all()
    """
    ...

def complete(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that marks a method as a component initialization handler
    for types registered with bridge_type().

    This decorator corresponds to QQmlParserStatus::componentComplete() in Qt.
    When QML instantiates a Python type registered through bridge_type(),
    the method decorated with @complete is automatically called after the
    component is fully constructed and all properties have been set.

    Parameters
    ----------
    func : Callable
        The initialization method to be called when the component is complete.
        Takes no arguments besides `self`.

    Notes
    -----
    - Only works with types registered via bridge_type(), not bridge_instance()
    - Called automatically by QML - you should not call it manually
    - Called after all property bindings have been established
    - Analogous to Component.onCompleted in QML

    Example
    -------
    >>> from QtBridge import bridge_type, complete
    >>>
    >>> class RestService:
    ...     def __init__(self):
    ...         self._url = ""
    ...         self._initialized = False
    ...
    ...     @property
    ...     def url(self) -> str:
    ...         return self._url
    ...
    ...     @url.setter
    ...     def url(self, value: str):
    ...         self._url = value
    ...
    ...     @complete
    ...     def componentComplete(self):
    ...         '''Called after QML sets all properties'''
    ...         print(f"Service initialized with URL: {self._url}")
    ...         self._initialized = True
    ...
    ...     def data(self) -> list:
    ...         return []
    >>>
    >>> bridge_type(RestService, uri="backend", version="1.0")

    In QML:
    >>> # RestService QML instantiation
    >>> import backend 1.0
    >>>
    >>> RestService {
    ...     url: "https://api.example.com"
    ...     // componentComplete() is called here automatically
    ...     // after url property is set
    ... }
    """
    ...
