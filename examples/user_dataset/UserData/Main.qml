// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import backend 1.0

ApplicationWindow {
    visible: true
    width: 1140
    height: 600
    title: "User List"
    color: "#2A2A2A"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Column names are read from headerData() provided by the QtBridge QAIM
        HorizontalHeaderView {
            id: horizontalHeader
            syncView: tableView
            Layout.fillWidth: true
            clip: true

            delegate: Rectangle {
                implicitHeight: 36
                color: "#404040"
                border.color: "#555555"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: display
                    font.bold: true
                    color: "#FFFFFF"
                    font.pixelSize: 12
                }
            }
        }

        TableView {
            id: tableView
            Layout.fillWidth: true
            Layout.fillHeight: true
            columnSpacing: 1
            rowSpacing: 1
            clip: true

            model: UserData

            columnWidthProvider: function(column) {
                var widths = [100, 130, 45, 155, 60, 175, 135, 90, 90, 155, 90]
                return widths[column] !== undefined ? widths[column] : 100
            }

            delegate: Rectangle {
                implicitHeight: 44
                color: (row % 2 === 0) ? "#2A2A2A" : "#333333"
                border.color: "#444444"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    anchors.margins: 4

                    text: {
                        // is_active column (index 4): render as Active / Inactive
                        if (column === 4)
                            return display ? "Active" : "Inactive"
                        return display !== undefined ? display : ""
                    }

                    color: {
                        if (column === 4)
                            return display ? "#00FF00" : "#FF6666"
                        return "#FFFFFF"
                    }

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    wrapMode: Text.WordWrap
                    font.pixelSize: 12
                }
            }
        }
    }
}
