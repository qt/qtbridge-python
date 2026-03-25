# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
Demonstrates loading and controlling QtQuick Controls widgets entirely from Python.

A Slider and two Labels are created from Python using load_qml_component(),
parented into the ApplicationWindow, and then driven by Python:

  - The Slider's value is animated forward by a QTimer.
  - A value Label updates in real-time when the Slider changes (via signal).
  - A status Label is updated by Python to show what's happening.

Controls are all created from Python.
"""
import sys

from PySide6.QtCore import QTimer

from QtBridge import load_qml_component, qtbridge

Slider = load_qml_component(module="QtQuick.Controls", type_name="Slider")
Label = load_qml_component(module="QtQuick.Controls", type_name="Label")
Button = load_qml_component(module="QtQuick.Controls", type_name="Button")

# Module-level reference keeps the QTimer alive for the application lifetime.
_timer: QTimer | None = None


@qtbridge(qml_file="Main.qml")
def main(window):
    """Called automatically by @qtbridge after the QML window is ready."""
    content = window.contentItem  # drawable area inside the window
    win_w = window.width           # 420

    # Python controls — properties are set directly on the QmlObject wrapper.
    heading = Label.create(text="Qt Controls — driven from Python")
    heading.parent = content
    heading.x = 20
    heading.y = 20

    slider = Slider.create()
    slider.parent = content
    slider.x = 20
    slider.y = 70
    slider.width = win_w - 40
    # Slider range 0.0 – 1.0 (the default), step size 0.01
    slider.stepSize = 0.01

    value_label = Label.create(text="Value: 0.00")
    value_label.parent = content
    value_label.x = 20
    value_label.y = 130

    def on_value_changed() -> None:
        value_label.text = f"Value: {slider.value:.2f}"

    slider.valueChanged.connect(on_value_changed)

    reset_btn = Button.create(text="Reset")
    reset_btn.parent = content
    reset_btn.x = 20
    reset_btn.y = 180

    status_label = Label.create(text="Status: animating…")

    def on_reset() -> None:
        slider.value = 0.0
        status_label.text = "Status: reset by Python"

    reset_btn.clicked.connect(on_reset)

    status_label.parent = content
    status_label.x = 120
    status_label.y = 184

    step = [0.0]

    def advance() -> None:
        step[0] += 0.02
        if step[0] > 1.0:
            step[0] = 0.0
        slider.value = step[0]
        status_label.text = "Status: animating…"
        print(f"Slider value set to {step[0]:.2f} from Python")

    global _timer
    _timer = QTimer()
    _timer.timeout.connect(advance)
    _timer.start(50)


if __name__ == "__main__":
    sys.exit(main())
