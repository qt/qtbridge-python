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
    """Called automatically by @qtbridge after the QML window is ready.

    TODO: Remove after updating to 6.11
    Returns the created QML objects so that @qtbridge's _keep_alive list
    holds references on PySide6 < 6.11 (where QQmlComponent::create() does not 
    transfer Python ownership).  On 6.11+ this is not needed.
    """
    content = window.property("contentItem") # drawable area inside the window
    win_w = window.property("width")     # 420
    
    # Python controls
    heading = Label.create(text="Qt Controls — driven from Python")
    heading.qobject.setProperty("parent", content)
    heading.qobject.setProperty("x", 20)
    heading.qobject.setProperty("y", 20)

    slider = Slider.create()
    slider.qobject.setProperty("parent", content)
    slider.qobject.setProperty("x", 20)
    slider.qobject.setProperty("y", 70)
    slider.qobject.setProperty("width", win_w - 40)
    # Slider range 0.0 – 1.0 (the default), step size 0.01
    slider.qobject.setProperty("stepSize", 0.01)

    value_label = Label.create(text="Value: 0.00")
    value_label.qobject.setProperty("parent", content)
    value_label.qobject.setProperty("x", 20)
    value_label.qobject.setProperty("y", 130)

    def on_value_changed() -> None:
        value_label.text = f"Value: {slider.value:.2f}"

    slider.qobject.valueChanged.connect(on_value_changed)

    reset_btn = Button.create(text="Reset")
    reset_btn.qobject.setProperty("parent", content)
    reset_btn.qobject.setProperty("x", 20)
    reset_btn.qobject.setProperty("y", 180)

    status_label = Label.create(text="Status: animating…")

    def on_reset() -> None:
        slider.value = 0.0
        status_label.text = "Status: reset by Python"

    reset_btn.qobject.clicked.connect(on_reset)

    status_label.qobject.setProperty("parent", content)
    status_label.qobject.setProperty("x", 120)
    status_label.qobject.setProperty("y", 184)

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

    # Return all created QML objects.  On PySide6 < 6.11, @qtbridge stores
    # this list in _keep_alive so Python GC doesn't collect the wrappers
    # before the event loop exits.  On 6.11+, create() returns Python-owned 
    # wrappers so this is not needed.
    return [heading, slider, value_label, reset_btn, status_label]


if __name__ == "__main__":
    sys.exit(main())
