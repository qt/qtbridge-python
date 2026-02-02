# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import sys
from QtBridge import qtbridge, bridge_type, Signal

class CounterModel:
    countChanged = Signal(int)

    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value: int):
        if self._count != value:
            print(f"CounterModel count changed from {self._count} to {value}")
            self._count = value
            # Manually emit the signal instead of using the auto property change notification
            self.countChanged.emit(self._count)

@qtbridge(module="CounterModel")
def main():
    bridge_type(CounterModel, uri="backend", version="1.0")

if __name__ == "__main__":
    sys.exit(main())
