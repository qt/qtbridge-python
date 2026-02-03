// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import Qt.labs.qmlmodels
import backend 1.0

ApplicationWindow {
    visible: true
    width: 990 + 7  // Column width + border width
    height: 600
    title: "User List"
    color: "#2A2A2A"

    TableModel {
        id: tableModel

        TableModelColumn { display: "username" }
        TableModelColumn { display: "name" }
        TableModelColumn { display: "age" }
        TableModelColumn { display: "profession" }
        TableModelColumn { display: "is_active" }
        TableModelColumn { display: "email" }
        TableModelColumn { display: "phone" }
        TableModelColumn { display: "address" }
    }

    Repeater {
        model: UserData

        Item {
            Component.onCompleted: {
                tableModel.appendRow({
                    "username": model.username,
                    "name": model.name,
                    "age": model.age,
                    "profession": model.profession,
                    "is_active": model.is_active,
                    "email": model.contact.email,
                    "phone": model.contact.phone,
                    "address": model.address
                })
            }
        }
    }

    Column {
        anchors.fill: parent

        HorizontalHeaderView {
            id: horizontalHeader
            syncView: tableView
            width: parent.width

            delegate: Rectangle {
                implicitHeight: 40
                color: "#404040"
                border.color: "#555555"
                border.width: 1

                Column {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        width: parent.width
                        height: 40
                        border.color: "#555555"
                        color: "#404040"

                        Text {
                            anchors.centerIn: parent
                            text: {
                                var headers = ["Username", "Name", "Age", "Profession", "Status", "Email", "Phone", "Address"]
                                return headers[index]
                            }
                            font.bold: true
                            color: "#FFFFFF"
                        }
                    }
                }
            }
        }

        TableView {
            id: tableView
            width: parent.width
            height: parent.height - horizontalHeader.height
            columnSpacing: 1
            rowSpacing: 1
            clip: true

            model: tableModel

            columnWidthProvider: function(column) {
                var widths = [100, 120, 60, 150, 60, 170, 150, 180]
                return widths[column]
            }

            delegate: Rectangle {
                implicitWidth: 100
                implicitHeight:50
                color: (row % 2 == 0) ? "#2A2A2A" : "#333333"
                border.color: "#444444"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: {
                        if (column == 4) // Status
                            return display ? "Active" : "Inactive"
                        else if (column == 7) // Address
                            return display.street + ", " + display.postal_code  + "\n" + display.city + ", " + display.country

                        return display || ""
                    }

                    color: {
                        if (column == 4)
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
