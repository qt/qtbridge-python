// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

// Alternative version using text symbols instead of icon images
// Use this if you want to run without generating resources first

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import backend 1.0

ApplicationWindow {
    id: window
    width: 400
    height: 300
    visible: true
    title: "Counter Example"

    CounterModel {
        id: counterModel
        count: 5
    }

    Rectangle {
        anchors.fill: parent
        color: "white"

        Rectangle {
            anchors.centerIn: parent
            width: 320
            height: 160
            radius: 20
            color: "white"

            Row {
                anchors.centerIn: parent
                spacing: 40

                // Minus button
                Rectangle {
                    width: 60
                    height: 60
                    radius: 30
                    color: minusMouseArea.pressed ? "#e74c3c" : "#ec7063"

                    Text {
                        anchors.centerIn: parent
                        text: "−"  // Unicode minus sign
                        font.pixelSize: 36
                        font.bold: true
                        color: "white"
                    }

                    MouseArea {
                        id: minusMouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            if (counterModel.count > 0) {
                                counterModel.count = counterModel.count - 1
                                console.log("Count decremented to:", counterModel.count)
                            } else {
                                console.log("Count cannot be negative")
                            }
                        }
                    }
                }

                // Count display
                Text {
                    text: counterModel.count
                    font.pixelSize: 48
                    font.bold: true
                    color: "#667eea"
                    anchors.verticalCenter: parent.verticalCenter
                }

                // Plus button
                Rectangle {
                    width: 60
                    height: 60
                    radius: 30
                    color: plusMouseArea.pressed ? "#27ae60" : "#52c375"

                    Text {
                        anchors.centerIn: parent
                        text: "+"
                        font.pixelSize: 36
                        font.bold: true
                        color: "white"
                    }

                    MouseArea {
                        id: plusMouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            counterModel.count = counterModel.count + 1
                            console.log("Count incremented to:", counterModel.count)
                        }
                    }
                }
            }
        }

        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 20
            text: "Click + or − to change the count"
            font.pixelSize: 14
            color: "white"
            opacity: 0.8
        }
    }

    Component.onCompleted: {
        console.log("TestCounterModel UI loaded (text-based version)")
        console.log("Initial count:", counterModel.count)
    }
}
