// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtGraphs
import backend 1.0

ApplicationWindow {
    id: root
    width: 1200
    height: 700
    visible: true
    title: qsTr("Graph Model Data - QtBridge Example")

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        // Left side: Data table with two side-by-side lists
        Rectangle {
            SplitView.minimumWidth: 400
            SplitView.preferredWidth: 450
            color: "white"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                // Series 1 Table
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 5

                    // Series 1 Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        color: "#2196F3"

                        Row {
                            anchors.fill: parent
                            spacing: 0

                            Rectangle {
                                width: parent.width / 2
                                height: parent.height
                                color: "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: "X"
                                    color: "white"
                                    font.bold: true
                                }
                            }
                            Rectangle {
                                width: parent.width / 2
                                height: parent.height
                                color: "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: "Y"
                                    color: "white"
                                    font.bold: true
                                }
                            }
                        }
                    }

                    // Series 1 Data ListView
                    ListView {
                        id: series1ListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: Series1Data

                        delegate: Rectangle {
                            width: series1ListView.width
                            height: 30
                            color: index % 2 ? "#e3f2fd" : "#ffffff"
                            border.color: "#cccccc"
                            border.width: 1

                            Row {
                                anchors.fill: parent
                                spacing: 0

                                // X value
                                Rectangle {
                                    width: parent.width / 2
                                    height: parent.height
                                    color: "transparent"
                                    Text {
                                        anchors.centerIn: parent
                                        text: (model.x !== undefined && model.x !== null) ?
                                            model.x.toFixed(1) : ""
                                    }
                                }

                                // Y value
                                Rectangle {
                                    width: parent.width / 2
                                    height: parent.height
                                    color: "transparent"
                                    Text {
                                        anchors.centerIn: parent
                                        text: (model.y !== undefined && model.y !== null) ?
                                            model.y.toFixed(1) : ""
                                    }
                                }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {}
                    }
                }

                // Series 2 Table - using property access since we need series2
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 5

                    // Series 2 Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        color: "#FF5722"

                        Row {
                            anchors.fill: parent
                            spacing: 0

                            Rectangle {
                                width: parent.width / 2
                                height: parent.height
                                color: "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: "X"
                                    color: "white"
                                    font.bold: true
                                }
                            }
                            Rectangle {
                                width: parent.width / 2
                                height: parent.height
                                color: "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: "Y"
                                    color: "white"
                                    font.bold: true
                                }
                            }
                        }
                    }

                    // Series 2 Data ListView
                    ListView {
                        id: series2ListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: Series2Data

                        delegate: Rectangle {
                            width: series2ListView.width
                            height: 30
                            color: index % 2 ? "#ffebee" : "#ffffff"
                            border.color: "#cccccc"
                            border.width: 1

                            Row {
                                anchors.fill: parent
                                spacing: 0

                                // X value
                                Rectangle {
                                    width: parent.width / 2
                                    height: parent.height
                                    color: "transparent"
                                    Text {
                                        anchors.centerIn: parent
                                        text: (model.x !== undefined && model.x !== null) ?
                                            model.x.toFixed(1) : ""
                                    }
                                }

                                // Y value
                                Rectangle {
                                    width: parent.width / 2
                                    height: parent.height
                                    color: "transparent"
                                    Text {
                                        anchors.centerIn: parent
                                        text: (model.y !== undefined && model.y !== null) ?
                                            model.y.toFixed(1) : ""
                                    }
                                }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {}
                    }
                }
            }
        }

        // Right side: Chart view
        Rectangle {
            SplitView.fillWidth: true
            SplitView.minimumWidth: 500
            color: "#f5f5f5"

            GraphsView {
                id: graphsView
                anchors.fill: parent
                anchors.margins: 10
                theme: GraphsTheme {
                    colorScheme: Qt.Light
                }

                axisX: ValueAxis {
                    min: 0
                    max: 800
                    labelFormat: "%.0f"
                }

                axisY: ValueAxis {
                    min: 0
                    max: 100
                    labelFormat: "%.0f"
                }

                LineSeries {
                    id: lineSeries1
                    name: "Series 1"
                    color: "#2196F3"
                    width: 2
                }

                LineSeries {
                    id: lineSeries2
                    name: "Series 2"
                    color: "#FF5722"
                    width: 2
                }
            }
        }
    }

    function updateSeries1() {
        lineSeries1.clear()
        let count = Series1Data.rowCount()
        for (let i = 0; i < count; i++) {
            let point = Series1Data.get_point(i)
            lineSeries1.append(point.x, point.y)
        }
    }

    function updateSeries2() {
        lineSeries2.clear()
        let count = Series2Data.rowCount()
        for (let i = 0; i < count; i++) {
            let point = Series2Data.get_point(i)
            lineSeries2.append(point.x, point.y)
        }
    }

    Component.onCompleted: {
        console.log("Chart Model Data Example loaded")
        console.log("Series 1 points:", series1ListView.count)
        console.log("Series 2 points:", series2ListView.count)

        // Update chart series
        updateSeries1()
        updateSeries2()
    }
}
