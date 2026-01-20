# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""QtBridge port of the Model Data Charts example
   https://doc.qt.io/qt-6/qtcharts-modeldata-example.html"""

from dataclasses import dataclass
from random import randrange
from typing import List
from QtBridge import qtbridge, bridge_instance

@dataclass
class DataPoint:
    x: float
    y: float

    def __str__(self):
        return f"({self.x}, {self.y})"


class ChartDataModel:
    def __init__(self, series_data: List[DataPoint]):
        self._series = series_data

    def data(self) -> List[DataPoint]:
        return self._series

    @property
    def series(self) -> List[DataPoint]:
        """List of data points for this series"""
        return self._series

    def get_point(self, index: int) -> dict:
        """Get a data point at the specified index as a dictionary"""
        if 0 <= index < len(self._series):
            point = self._series[index]
            return {"x": point.x, "y": point.y}
        return {"x": -1, "y": -1}


@qtbridge(qml_file="Main.qml")
def main():
    # Generate random data
    row_count = 15
    series1_data = []
    series2_data = []

    for i in range(row_count):
        # Series 1: x values are multiples of 50 with small random offset
        x1 = i * 50 + randrange(30)
        y1 = randrange(100)
        series1_data.append(DataPoint(x1, y1))

        # Series 2: similar pattern but different values
        x2 = i * 50 + randrange(30)
        y2 = randrange(100)
        series2_data.append(DataPoint(x2, y2))

    series1_model = ChartDataModel(series1_data)
    series2_model = ChartDataModel(series2_data)

    bridge_instance(series1_model, name="Series1Data")
    bridge_instance(series2_model, name="Series2Data")


if __name__ == "__main__":
    main()
