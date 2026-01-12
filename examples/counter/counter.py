# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import sys

from QtBridge import qtbridge, bridge_type

class CounterModel:
    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        print(f"CounterModel count changed from {self._count} to {value}")
        self._count = int(value)

@qtbridge(module="CounterModel")
def main():
    bridge_type(CounterModel, uri="backend", version="1.0")

if __name__ == "__main__":
    sys.exit(main())
