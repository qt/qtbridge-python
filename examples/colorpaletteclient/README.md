# QtBridges ColorPalette Client Example

A QML-based color palette manager that demonstrates using QtBridges for connecting Python backends with QML frontends. This example showcases how you can build interactive UI applications using almost pure Python code with minimal boilerplate.

## Overview

The ColorPalette Client is a full-featured application that manages color palettes and user data through a REST API. It demonstrates:

- **Pure Python Models**: Define data models and business logic entirely in Python using dataclasses
- **Seamless QML Integration**: Expose Python classes, properties, and methods to QML automatically
- **REST API Integration**: Switch between a public demo API(regres.in) and a local editable backend
- **CRUD Operations**: Add, edit, delete, and paginate through colors and users
- **User Authentication**: Simple login system with session management

## Backend Options

You can choose between two REST API backends:

### 1. reqres.in Demo API
A public demo API available at `https://reqres.in` for testing purposes.
- Fetches color and user data
- **Does not support modifications** (add, edit, delete operations will appear to work but won't persist)

### 2. Local REST API
A FastAPI-based server included with this example that provides full functionality.
- Supports all CRUD operations (Create, Read, Update, Delete)
- Data persisted locally as JSON files
- Includes user authentication
- Best for experiencing the complete application workflow

## Prerequisites

- Python 3.9 or higher
- QtBridges installed (`pip install qtbridge`)

## Setup and Running

### Option 1: Using the Local REST Server (Recommended)

#### Step 1: Start the Local Server

Navigate to the server directory and install dependencies:

```bash
cd examples/colorpaletteclient/server
pip install -r requirements.txt
```

Make the script executable (Linux/macOS):

```bash
chmod +x start_server.sh
```

Start the server:

```bash
./start_server.sh
```

On Windows, run the server directly:

```powershell
uvicorn main:app --host 127.0.0.1 --port 49425
```
The server will start at `http://127.0.0.1:49425`

To stop the server, press `Ctrl+C` in the terminal where it is running.

#### Step 2: Run the Client Application

In a new terminal, install client dependencies:

```bash
pip install -r examples/colorpaletteclient/requirements.txt
```

Run the client:

```bash
python examples/colorpaletteclient/main.py
```

In the application, select "Local Server" from the server selection screen.

### Option 2: Using reqres.in Demo API

Install client dependencies:

```bash
pip install -r examples/colorpaletteclient/requirements.txt
```

Run the client:

```bash
python examples/colorpaletteclient/main.py
```

In the application, select "reqres.in" from the server selection screen.

**Note:** Modifications (add, edit, delete) will not persist when using the demo API.

## Features Demonstrated

### QtBridges APIs Used

- **`bridge_type()`**: Registers Python classes as QML types
- **`bridge_instance()`**: Exposes Python objects as QML singletons
- **`@reset` Decorator**: Manages QML model updates efficiently

## Key QtBridges Concepts Demonstrated

### 1. Minimal Boilerplate
Unlike traditional PySide6 where you need to define `@Property`, `@Signal`,
and `@Slot` decorators, QtBridges automatically:
- Exposes public methods to QML
- Handles property bindings
- Manages signal connections

Note: point to PySide6 example somewhere here

### 2. Python-First Development
Write your business logic in pure Python using familiar patterns (dataclasses, type hints), and QtBridges handles the QML integration.

### 3. Automatic Type Conversion
QtBridges automatically converts between Python types and QML types:
```python
def data(self) -> list[ColorUser]:  # Type hints guide conversion
    return self._users
```
