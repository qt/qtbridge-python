# Qt Bridge - Python

> Copyright (C) 2025 The Qt Company Ltd.
> SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

## About

Qt Bridges is a framework that simplifies the integration of Python with
[QtQuick/QML](https://doc.qt.io/qt-6/qtquick-index.html). It connects Python backends to QML
frontends, improving development efficiency. The framework offers an easy, declarative method for
linking Python classes, properties, signals, and slots to QML, with minimal Qt knowledge required
from the Python developer.

### Why a Python Qt Bridge?

As a Python developer, you can expose your Python classes to QML without learning the full [Qt for
Python (PySide6)](https://doc.qt.io/qtforpython-6/) model/view system. Qt Bridges automatically
handles property binding, signal connections, and model registration.

* Less boilerplate: No manual `@Slot`, `@Property`, or signal management required
* Automatic discovery: Public methods become callable from QML automatically
* Model integration: Python classes become QML-ready models with simple decorators
* Cross-language: Reuse the same QML files across multiple languages supported by Qt Bridges.

## Prerequisites

This projects needs Python 3.9+ installed in your system, including `pip`.
The dependencies are fetched at build time, and are included in the `pyproject.toml`
file.

When building you will need:

* CMake: Minimum version 3.18
* Qt: Minimum version 6.10
* PySide6 and Shiboken6: Install version `6.10` before building with `pip install PySide6==6.10`
* Build system: `scikit-build-core` is used for building and packaging the project
* Documentation `QDoc` (Qt's built-in tool for generating API reference documentation)
* Testing: `pytest` framework with `pytest-qt` plugin

## Build & Install

When building from source, you can use `pip` in order to create the wheels
or install directly.

To create the wheels:

```
pip wheel . -Ccmake.define.QT_PATHS=/path/to/qtpaths
```

To build and install directly:

```
pip install . -Ccmake.define.QT_PATHS=/path/to/qtpaths

```

Future versions of this bridge will be available on PyPI, and you will be
able to install it using:

```
pip install qtbridge
```

### For developers

```
pip install -e ".[dev]"
```

### Running tests

```
pytest .
```

## Examples

Explore the following examples to get started with QtBridge for Python. Each example demonstrates
different features and capabilities. Check out the README.md in each example folder for detailed
information:

* [simple_app](examples/simple_app/) - A simple application to get you started with QtBridge
* [minimal_app](examples/minimal_app/) - Expands on simple_app application demonstrating CRUD
operations on a list
* [counter](examples/counter/) - Simple counter example with basic state management
* [quiz_example](examples/quiz_example/) - Interactive quiz application
* [colorpaletteclient](examples/colorpaletteclient/) - Advanced example with REST API integration
and color palette management

## Stay in touch

You can reach us in the Qt Forum, specifically in the [Qt Bridges
category](https://forum.qt.io/category/78/qt-bridges).

## Terms and Conditions

This is a pre-release implementation of Qt Bridges for Python. By installing this package, you agree
to the terms and conditions stated in https://www.qt.io/terms-conditions. These terms and conditions
also apply to the Qt Framework, which is used as a major dependency in this package.

The QtBridge for Python is built using PySide6, which is licensed under LGPLv3 or Commercial
licenses, see https://www.qt.io/development/qt-framework/qt-licensing

PySide6 provides optional support for NumPy. Applications built with QtBridge for Python and using
NumPy will include NumPy licensed under the modified BSD license