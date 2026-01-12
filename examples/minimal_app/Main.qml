// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import backend 1.0

ApplicationWindow {
    id: root

    width: 640
    height: 480
    visible: true
    title: qsTr("String List Manager")

    ColumnLayout {
        id: mainLayout
        anchors.fill: parent
        anchors.margins: 10

        ListView {
            id: lv
            model: String_model
            clip: true
            spacing: 5

            delegate: Rectangle {
                id: itemRect

                required property int index
                required property string display

                width: lv.width
                height: 50
                color: "transparent"
                border.color: "lightgray"
                border.width: 1
                radius: 5

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 5

                    TextField {
                        id: textInput
                        text: itemRect.display
                        selectByMouse: true
                        Layout.fillWidth: true

                        background: Rectangle {
                            color: "transparent"
                        }

                        onEditingFinished: {
                            if (text !== itemRect.display) {
                                String_model.set_item(itemRect.index, text)
                            }
                        }
                    }

                    Button {
                        text: "×"
                        font.pixelSize: 20
                        flat: true

                        onClicked: {
                            String_model.delete_string(itemRect.index)
                        }

                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                    }
                }
            }
            Layout.fillHeight: true
            Layout.preferredWidth: mainLayout.width
        }

        RowLayout {
            implicitHeight: Math.max(input.implicitHeight, submitButton.implicitHeight)
            TextField {
                id: input
                placeholderText: "Enter string to add"
                onAccepted: {
                    if (input.text !== "") {
                        String_model.add_string(input.text)
                        input.clear()
                    }
                }
                Layout.preferredWidth: mainLayout.width * 0.8
            }
            Button {
                id: submitButton
                text: "Add"
                enabled: input.text !== ""
                onReleased: {
                    String_model.add_string(input.text)
                    input.clear()
                }
            }
        }
    }
}
