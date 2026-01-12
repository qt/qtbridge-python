# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from QtBridge import bridge_instance, qtbridge

import os
pid = os.getpid()


@qtbridge(module="Main")
def main():
    fruits_list = ["apple", "banana", "cherry"]
    fruits_tuple = ("apple", "banana", "cherry")
    # QML requires type names to start with an uppercase letter
    bridge_instance(fruits_tuple, name="String_model")


if __name__ == "__main__":
    main()
