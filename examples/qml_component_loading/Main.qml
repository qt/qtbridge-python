// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root

    width: 400
    height: 300
    visible: true
    title: qsTr("QML Composition Example")

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 20

        Label {
            text: "QML Composition from Python"
            font.pixelSize: 20
            Layout.alignment: Qt.AlignHCenter
        }

        Label {
            text: "This window confirms the @qtbridge engine is running.\n"
                  + "Check the terminal for composition output."
            horizontalAlignment: Text.AlignHCenter
            Layout.alignment: Qt.AlignHCenter
        }
    }
}
