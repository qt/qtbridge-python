# Graphs Line Series Data Example

This example demonstrates how to use QtBridges with QtGraphs to visualize data from Python models as
line series in QML.

## Functionality

- Generates random data points in Python using dataclasses
- Exposes two data series to QML as model instances
- Displays data in side-by-side tables
- Renders the same data as line charts using QtGraphs LineSeries
- Demonstrates seamless integration between Python data models and Qt Graphs components

## Purpose

This example shows how to use `bridge_instance()` to expose Python data models to QML and integrate
them with Qt Graphs for data visualization.

## Key Concepts

### 1. Exposing Python Data to QML

In the Python backend (`main.py`):

```python
from dataclasses import dataclass
from typing import List
from QtBridge import qtbridge, bridge_instance

@dataclass
class DataPoint:
    x: float
    y: float

class ChartDataModel:
    def __init__(self, series_data: List[DataPoint]):
        self._series = series_data

    def data(self) -> List[DataPoint]:
        return self._series

    def get_point(self, index: int) -> dict:
        # Returns a point as a dictionary for easy QML access
        if 0 <= index < len(self._series):
            point = self._series[index]
            return {"x": point.x, "y": point.y}
        return {"x": -1, "y": -1}

@qtbridge(qml_file="Main.qml")
def main():
    series1_model = ChartDataModel(series1_data)
    series2_model = ChartDataModel(series2_data)

    bridge_instance(series1_model, name="Series1Data")
    bridge_instance(series2_model, name="Series2Data")
```

The `bridge_instance()` calls make the Python model objects available in QML as `Series1Data` and
`Series2Data`.

### 2. Using Python Data with QtGraphs in QML

In the QML file (`Main.qml`):

```qml
import QtGraphs
import backend 1.0

GraphsView {
    LineSeries {
        id: lineSeries1
        name: "Series 1"
    }

    LineSeries {
        id: lineSeries2
        name: "Series 2"
    }
}

function updateSeries1() {
    lineSeries1.clear()
    let count = Series1Data.rowCount()
    for (let i = 0; i < count; i++) {
        let point = Series1Data.get_point(i)
        lineSeries1.append(point.x, point.y)
    }
}
```

The Python models are used both as ListView models for the data tables and as data sources for the
chart series.

## Running the Example

```bash
python main.py
```

## Summary

This example demonstrates QtBridges' flexibility in working with other Qt modules like QtGraphs,
showing how Python data models can power both traditional list views and graph visualizations with
minimal code.
