# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import sys
from QtBridge import qtbridge, bridge_type, watch, effect, Change


class CounterModel:
    def __init__(self):
        self.count = 0  # auto-property

    @watch("count")
    def _log_count_change(self, change: Change) -> None:
        print(f"[watch] count changed: {change.old} → {change.new}")

    @effect("count")
    def _check_milestone(self) -> None:
        milestones = {
            5:  "High five! 🖐",
            10: "Perfect ten! 🎯",
            20: "Score of 20 — to the moon! 🚀",
        }
        if self.count in milestones:
            print(f"[effect] Milestone: {milestones[self.count]}")


@qtbridge(module="CounterModel")
def main():
    bridge_type(CounterModel, uri="backend", version="1.0")

if __name__ == "__main__":
    sys.exit(main())
