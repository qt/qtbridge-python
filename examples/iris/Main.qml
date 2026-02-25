// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import backend 1.0

ApplicationWindow {
    id: root
    width: 960
    height: 680
    visible: true
    title: "Iris Dataset — DuckDB + Polars + QtBridge"
    color: "#1e1e2e"

    property int selectedRow: -1

    readonly property color accentColor:  "#89b4fa"
    readonly property color surfaceColor: "#313244"
    readonly property color baseColor:    "#1e1e2e"
    readonly property color textColor:    "#cdd6f4"
    readonly property color subtextColor: "#a6adc8"
    readonly property color redColor:     "#f38ba8"
    readonly property color greenColor:   "#a6e3a1"
    readonly property color yellowColor:  "#f9e2af"
    readonly property color overlayColor: "#45475a"

    header: ToolBar {
        background: Rectangle { color: root.surfaceColor }
        height: 56

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 12

            Label {
                text: "🌸 Iris Dataset"
                font.pixelSize: 18
                font.bold: true
                color: root.accentColor
            }

            Label {
                text: IrisData.row_count() + " records"
                font.pixelSize: 13
                color: root.subtextColor
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "＋ Add"
                font.pixelSize: 13
                onClicked: addDialog.open()
                background: Rectangle {
                    radius: 6
                    color: parent.hovered ? Qt.lighter(root.greenColor, 1.15)
                                          : root.greenColor
                }
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: root.baseColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Button {
                text: "✎ Edit"
                font.pixelSize: 13
                enabled: root.selectedRow >= 0
                onClicked: {
                    let row = IrisData.get_row(root.selectedRow)
                    editSlField.text  = String(row.sepal_length ?? "")
                    editSwField.text  = String(row.sepal_width  ?? "")
                    editPlField.text  = String(row.petal_length ?? "")
                    editPwField.text  = String(row.petal_width  ?? "")
                    editSpecies.currentIndex = editSpecies.find(row.species ?? "")
                    editDialog.open()
                }
                opacity: enabled ? 1.0 : 0.4
                background: Rectangle {
                    radius: 6
                    color: parent.hovered ? Qt.lighter(root.yellowColor, 1.15)
                                          : root.yellowColor
                }
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: root.baseColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Button {
                text: "✕ Delete"
                font.pixelSize: 13
                enabled: root.selectedRow >= 0
                onClicked: deleteDialog.open()
                opacity: enabled ? 1.0 : 0.4
                background: Rectangle {
                    radius: 6
                    color: parent.hovered ? Qt.lighter(root.redColor, 1.15)
                                          : root.redColor
                }
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: root.baseColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        HorizontalHeaderView {
            id: headerView
            syncView: tableView // sync with tableView for headers
            Layout.fillWidth: true
            clip: true

            delegate: Rectangle {
                implicitHeight: 36
                color: root.surfaceColor
                border.color: root.overlayColor
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: display
                    font.bold: true
                    font.pixelSize: 12
                    color: root.accentColor
                }
            }
        }

        TableView {
            id: tableView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            model: IrisData // our registered Python instance

            columnWidthProvider: function (column) {
                // 5 columns
                var widths = [160, 160, 160, 160, 160]
                if (column < widths.length)
                    return Math.max(widths[column], tableView.width / 5)
                return 100
            }

            delegate: Rectangle {
                implicitHeight: 38
                color: row === root.selectedRow
                       ? Qt.rgba(root.accentColor.r, root.accentColor.g,
                                 root.accentColor.b, 0.25)
                       : (row % 2 === 0 ? root.baseColor : root.surfaceColor)
                border.color: root.overlayColor
                border.width: 0.5

                Text {
                    anchors.centerIn: parent
                    text: display !== undefined ? display : ""
                    font.pixelSize: 13
                    color: {
                        if (column === 4) {
                            if (display === "setosa")     return root.greenColor
                            if (display === "versicolor") return root.yellowColor
                            if (display === "virginica")  return root.redColor
                        }
                        return root.textColor
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        root.selectedRow = (root.selectedRow === row) ? -1 : row
                    }
                }
            }
        }
    }

    footer: ToolBar {
        background: Rectangle { color: root.surfaceColor }
        height: 32

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16

            Label {
                text: root.selectedRow >= 0
                      ? "Selected row: " + (root.selectedRow + 1)
                      : "Click a row to select it"
                font.pixelSize: 12
                color: root.subtextColor
            }

            Item { Layout.fillWidth: true }

            Label {
                text: "Powered by DuckDB + Polars"
                font.pixelSize: 11
                font.italic: true
                color: root.overlayColor
            }
        }
    }

    Dialog {
        id: addDialog
        title: "Add New Iris Record"
        anchors.centerIn: parent
        width: 380
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        background: Rectangle {
            color: root.surfaceColor
            radius: 10
            border.color: root.overlayColor
        }
        header: Label {
            text: addDialog.title
            font.pixelSize: 16
            font.bold: true
            color: root.accentColor
            padding: 16
            background: Rectangle { color: "transparent" }
        }

        onAccepted: {
            IrisData.add_row(
                parseFloat(addSlField.text),
                parseFloat(addSwField.text),
                parseFloat(addPlField.text),
                parseFloat(addPwField.text),
                addSpecies.currentText
            )
            // Select the newly added row (last row)
            root.selectedRow = IrisData.row_count() - 1
            addSlField.text = ""; addSwField.text = ""
            addPlField.text = ""; addPwField.text = ""
            addSpecies.currentIndex = 0
        }
        onRejected: {
            addSlField.text = ""; addSwField.text = ""
            addPlField.text = ""; addPwField.text = ""
            addSpecies.currentIndex = 0
        }

        GridLayout {
            columns: 2
            columnSpacing: 12
            rowSpacing: 10
            width: parent.width

            Label { text: "Sepal Length"; color: root.textColor }
            TextField {
                id: addSlField
                placeholderText: "e.g. 5.1"
                Layout.fillWidth: true
                color: root.textColor
                placeholderTextColor: root.overlayColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Sepal Width"; color: root.textColor }
            TextField {
                id: addSwField
                placeholderText: "e.g. 3.5"
                Layout.fillWidth: true
                color: root.textColor
                placeholderTextColor: root.overlayColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Petal Length"; color: root.textColor }
            TextField {
                id: addPlField
                placeholderText: "e.g. 1.4"
                Layout.fillWidth: true
                color: root.textColor
                placeholderTextColor: root.overlayColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Petal Width"; color: root.textColor }
            TextField {
                id: addPwField
                placeholderText: "e.g. 0.2"
                Layout.fillWidth: true
                color: root.textColor
                placeholderTextColor: root.overlayColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Species"; color: root.textColor }
            ComboBox {
                id: addSpecies
                model: ["setosa", "versicolor", "virginica"]
                Layout.fillWidth: true
            }
        }
    }

    Dialog {
        id: editDialog
        title: "Edit Iris Record (row " + (root.selectedRow + 1) + ")"
        anchors.centerIn: parent
        width: 380
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        background: Rectangle {
            color: root.surfaceColor
            radius: 10
            border.color: root.overlayColor
        }
        header: Label {
            text: editDialog.title
            font.pixelSize: 16
            font.bold: true
            color: root.yellowColor
            padding: 16
            background: Rectangle { color: "transparent" }
        }

        onAccepted: {
            IrisData.update_row(
                root.selectedRow,
                parseFloat(editSlField.text),
                parseFloat(editSwField.text),
                parseFloat(editPlField.text),
                parseFloat(editPwField.text),
                editSpecies.currentText
            )
        }

        GridLayout {
            columns: 2
            columnSpacing: 12
            rowSpacing: 10
            width: parent.width

            Label { text: "Sepal Length"; color: root.textColor }
            TextField {
                id: editSlField
                Layout.fillWidth: true
                color: root.textColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Sepal Width"; color: root.textColor }
            TextField {
                id: editSwField
                Layout.fillWidth: true
                color: root.textColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Petal Length"; color: root.textColor }
            TextField {
                id: editPlField
                Layout.fillWidth: true
                color: root.textColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Petal Width"; color: root.textColor }
            TextField {
                id: editPwField
                Layout.fillWidth: true
                color: root.textColor
                background: Rectangle {
                    radius: 4; color: root.baseColor
                    border.color: root.overlayColor
                }
            }

            Label { text: "Species"; color: root.textColor }
            ComboBox {
                id: editSpecies
                model: ["setosa", "versicolor", "virginica"]
                Layout.fillWidth: true
            }
        }
    }

    Dialog {
        id: deleteDialog
        title: "Delete Row"
        anchors.centerIn: parent
        width: 340
        modal: true
        standardButtons: Dialog.Yes | Dialog.No

        background: Rectangle {
            color: root.surfaceColor
            radius: 10
            border.color: root.overlayColor
        }
        header: Label {
            text: deleteDialog.title
            font.pixelSize: 16
            font.bold: true
            color: root.redColor
            padding: 16
            background: Rectangle { color: "transparent" }
        }

        Label {
            text: "Delete row " + (root.selectedRow + 1) + "?"
            color: root.textColor
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            width: parent.width
        }

        onAccepted: {
            IrisData.delete_row(root.selectedRow)
            root.selectedRow = -1
        }
    }

    Component.onCompleted: {
        console.log("Iris CRUD loaded —", IrisData.row_count(), "records")
    }
}
