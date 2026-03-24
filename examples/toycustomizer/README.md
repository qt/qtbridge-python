# ToyCustomizer — QtBridge Python Port

A Python port of the Qt Quick 3D ToyCustomizer demo.
The 3D scene and almost all UI layout QML files are kept intact. Data models,
business logic (pricing, accessory selection, name-picking) and state management
have been moved into a Python backend connected to QML via **QtBridge**.

All static data, application state, and business logic that was previously
spread across QML singleton files and C++ models has been moved to plain Python
dataclasses and backend classes. A small number of QML files were also adjusted
to fix desktop-specific behaviour not present in the original demo; these
differences are listed below.

## Prerequisites

- Python 3.10+
- QtBridge installed (see the repo root `README.md`)
- PySide6 > 6.11 with Qt Quick 3D support

## First Run — Assets

The binary assets (meshes, textures, fonts, animations) are not committed to
the repository. On first run, `main.py` will automatically download and
extract the required assets into the `ToyCustomizer/` directory if they are not
already present, so you do not need to run `fetch_assets.py` manually. If you
prefer to pre-download them, run:

```bash
python fetch_assets.py
```

This places `images/`, `meshes/`, `fonts/`, and `animations/` inside
`ToyCustomizer/` so that the QML relative-path references resolve correctly.

## Launch

```bash
python main.py
```

## Architecture

| File | Role |
|---|---|
| `models.py` | `@dataclass` types: `Toy`, `Accessory`, `NamePart`, `AnimalConfig` |
| `toy_catalog.py` | 14 toy entries → `ToyModelData` QML singleton |
| `animation_config.py` | 14 per-animal 3D configs → `AnimationModelData` QML singleton |
| `accessory_model.py` | Accessory selection + color logic → `AccessoryModelData` |
| `name_model.py` | Adjective/noun name-picker → `NameModelData` |
| `order_model.py` | Pricing & order summary → `OrderData` |
| `fetch_assets.py` | One-shot asset downloader |
| `main.py` | Entry point: registers all backends and launches the QML engine |
| `ToyCustomizer/qmldir` | QML module declaration |
| `ToyCustomizer/qml/` | All QML files (3D scenes + UI), mostly unchanged from C++ |

### What moved to Python

- **Toy catalogue** (`ToyModel.qml` → `toy_catalog.py`)
- **Animal 3D config** (`AnimationModel.qml` → `animation_config.py`)
- **Accessory selection logic** (JS in `AccessoryView.qml` →
    `accessory_model.py`)
- **Name-picker selection** (JS in `NameTumbler.qml` → `name_model.py`)
- **Order/pricing calculation** (`pickSelected()` JS in `OrderGrid.qml` →
    `order_model.py`)

### What stayed in QML

- All 3D scene files (`ToyCustom.qml`, `ToyAnimations.qml`, `ShowcaseView.qml`,
    etc.)
- `AccessoryState.qml` — All `bool` visibility properties bound directly to 3D
    `Model.visible`; Python drives them via the `accessory_visibility_changed(key,
    bool)` signal
- `ApplicationConfig.qml` — uses `Screen`, `Window`, and Qt-native font metrics
- All layout and UI component files

## Changes from the QML Original

### Removed QML files
- `ToyModel.qml` — replaced by `ToyModelBackend` in `toy_catalog.py`.
- `AnimationModel.qml` — replaced by `AnimationConfigBackend` in
    `animation_config.py`.
- `AccessoryModel.qml` — split into `AccessoryModelBackend`
    (`accessory_model.py`) and `NameModelBackend` (`name_model.py`).

### Modified QML files
- `Main.qml` — replaced inline `AccessoryModel` instantiation with the
    `AccessoryModelData` singleton and added a `Connections` block to forward the
    `accessory_visibility_changed(key, bool)` signal to `AccessoryState`.
- `ToyGalleryPage.qml` — `model: ToyModel` changed to `model: ToyModelData`.
- `ToyConfirmPage.qml` — all `ToyModel` references replaced with the
    `ToyModelData` singleton; content wrapped in a `ScrollView` to allow scrolling
    on smaller desktop windows.
- `AccessoryView.qml` — delegate JS calls (`select`, `deselect`, `setColor`)
    replaced with Python method calls on `AccessoryModelData`; added
    `absoluteIndex()` to map proxy rows to source indices, and set
    `interactive: tabBar.currentIndex !== 4` on the `ListView` to avoid stealing
    events from `NameTumbler` when hidden (enables scrolling).
- `NameTumbler.qml` — two `SortFilterProxyModel` components removed; replaced
    with `NameModelData.adjectives()` and `NameModelData.nouns()` Python method
    calls; `wrap: false` set on both `Tumbler` items to avoid `DragHandler`
    conflict with `OrbitCameraController` on desktop.
- `OrderGrid.qml` — `pickSelected()` JS function removed; all slot data bound
    directly to `OrderData.*` auto-properties.
- `CurrentToyModel.qml` and `ToyAnimations.qml` — `AnimationModel` references
    replaced with the `AnimationModelData` singleton.
- `ToyCustomizePage.qml` — inline `AccessoryModel` instantiation removed;
    `resetAllAccessories()` replaced with `AccessoryModelData.reset_all()`; both
    portrait `ColumnLayout` and landscape `RowLayout` wrapped in `ScrollView` with
    explicit `contentHeight` to allow scrolling.
- `AccessoryMaterialLibrary.qml` — `accessoryModel.colorOf(name)` replaced with
    `AccessoryModelData.color_of(name)`.
