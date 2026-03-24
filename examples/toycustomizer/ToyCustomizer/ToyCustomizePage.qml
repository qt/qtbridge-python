// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import backend 1.0

Item {
    id: toyCustomizePage

    property alias toyIndex: toyView.toyIndex
    property bool reset: false
    required property var accessoryModel

    signal cancelled
    signal confirmed
    signal showMaximizeViewRequested(page: Component)
    signal hideMaximizeViewRequested

    Component.onCompleted: {
        if (reset)
            AccessoryModelData.reset_all()
    }

    ScrollView {
        id: portraitScrollView
        visible: ApplicationConfig.isPortrait
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: portraitGridLayout.implicitHeight

        ColumnLayout {
            id: portraitGridLayout
            width: portraitScrollView.availableWidth

            LayoutItemProxy {
                target: toyView
                Layout.fillWidth: true
                Layout.preferredWidth: ApplicationConfig.responsiveSize(1051)
                Layout.preferredHeight: ApplicationConfig.responsiveSize(1181)
                Layout.leftMargin: ApplicationConfig.responsiveSize(100)
                Layout.rightMargin: ApplicationConfig.responsiveSize(100)
            }

            LayoutItemProxy {
                target: accessoryView
                Layout.fillWidth: true
            }
        }
    }

    ScrollView {
        id: landscapeScrollView
        visible: !ApplicationConfig.isPortrait
        anchors {
            fill: parent
            leftMargin: ApplicationConfig.responsiveSize(100)
            rightMargin: ApplicationConfig.responsiveSize(100)
        }
        contentWidth: availableWidth
        contentHeight: landscapeLayout.implicitHeight

        RowLayout {
            id: landscapeLayout
            width: landscapeScrollView.availableWidth
            spacing: ApplicationConfig.responsiveSize(100)

            LayoutItemProxy {
                target: toyView
                implicitHeight: ApplicationConfig.responsiveSize(1602)
                Layout.fillWidth: true
            }

            LayoutItemProxy {
                target: accessoryView
                Layout.fillWidth: true
                Layout.preferredHeight: ApplicationConfig.responsiveSize(1366)
            }
        }
    }

    Component {
        id: maximizeView
        MaximizeView {
            accessoryModel: toyCustomizePage.accessoryModel
            toyIndex: toyCustomizePage.toyIndex
            onHideRequested: toyCustomizePage.hideMaximizeViewRequested()
        }
    }

    ToyView {
        id: toyView
        implicitWidth: ApplicationConfig.responsiveSize(2080)
        accessoryModel: AccessoryModelData
        onHideRequested: toyCustomizePage.cancelled()
        onShowRequested: toyCustomizePage.showMaximizeViewRequested(maximizeView)
        onConfirmRequested: toyCustomizePage.confirmed()
    }

    AccessoryView {
        id: accessoryView
        implicitWidth: ApplicationConfig.responsiveSize(2080)
        target: toyView.toy
        model: AccessoryModelData
    }
}
