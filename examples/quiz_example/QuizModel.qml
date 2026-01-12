// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models
import backend 1.0

ApplicationWindow {
    visible: true
    width: 440
    height: 200
    title: "Dev Jokes"

    // Neon accent colors
    property var accentColors: ["#FF6F61", "#64FFDA", "#82B1FF", "#FFAB40", "#EA80FC"]
    property int currentIndex: Math.floor(Math.random() * QA_model.rowCount())
    property bool showingAnswer: false

    // Dark background
    Rectangle {
        anchors.fill: parent
        color: '#1E1E1E'
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 20
        width: parent.width * 0.9

        Rectangle {
            id: card
            radius: 12
            color: "#1E1E1E"
            Layout.fillWidth: true
            height: 90

            Text {
                id: displayText
                text: QA_model.getItem(currentIndex, 0)
                anchors.centerIn: parent
                width: parent.width * 0.9
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
                font.weight: Font.Medium
                color: "#E0E0E0"
            }
        }

        Button {
            id: actionButton
            text: showingAnswer ? "Another One" : "See Answer"
            Layout.alignment: Qt.AlignHCenter
            padding: 12

            font.pixelSize: 18
            font.weight: Font.DemiBold

            background: Rectangle {
                radius: 10
                color: actionButton.down ? "#333333" : "#262626"
                border.color: "#3f3f3f"
                border.width: 1
            }

            contentItem: Text {
                text: actionButton.text
                anchors.centerIn: parent
                color: "#E0E0E0"
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }

            onClicked: {
                if (!showingAnswer) {
                    // neon color for answer
                    let idx = Math.floor(Math.random() * accentColors.length)
                    displayText.color = accentColors[idx]

                    displayText.text = QA_model.getItem(currentIndex, 1)
                    showingAnswer = true
                } else {
                    displayText.color = "#E0E0E0"
                    currentIndex = Math.floor(Math.random() * QA_model.rowCount())
                    displayText.text = QA_model.getItem(currentIndex, 0)
                    showingAnswer = false
                }
            }
        }
    }
}
