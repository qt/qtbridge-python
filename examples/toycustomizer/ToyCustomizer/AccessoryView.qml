// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.impl
import backend 1.0

Rectangle {
    id: accessoryView

    property alias model: groupFilterProxyModel.model
    property var target: null
    property real horizontalPaddings: ApplicationConfig.responsiveSize(120)
    property real verticalPaddings: ApplicationConfig.responsiveSize(100)

    color: "#FFFFFF"
    clip: true
    topLeftRadius: ApplicationConfig.responsiveSize(56)
    topRightRadius: ApplicationConfig.responsiveSize(56)
    bottomLeftRadius: ApplicationConfig.isPortrait ? 0 : ApplicationConfig.responsiveSize(56)
    bottomRightRadius: ApplicationConfig.isPortrait ? 0 : ApplicationConfig.responsiveSize(56)

    implicitHeight: {
        const tabBarHeight = tabBar.implicitHeight + ApplicationConfig.responsiveSize(120)
        const listViewHeight = listView.implicitHeight + ApplicationConfig.responsiveSize(200)
        return tabBarHeight + listViewHeight
    }

    component AccessoryTabButton: TabButton {
        id: tabButton

        readonly property color color: tabButton.checked ? "#EFF7FF" : "#6A6A8D"

        width: Math.max(tabBar.width / 5, ApplicationConfig.responsiveSize(415))
        height: tabBar.height

        font {
            family: "Winky Sans"
            pixelSize: Math.round(ApplicationConfig.responsiveSize(48))
            weight: tabButton.checked ? Font.Bold : Font.Normal
        }

        icon {
            width: ApplicationConfig.responsiveSize(36)
            height: ApplicationConfig.responsiveSize(36)
            color: tabButton.color
        }

        contentItem: IconLabel {
            id: contentItem
            font: tabButton.font
            icon: tabButton.icon
            text: tabButton.text
            color: tabButton.color
            spacing: ApplicationConfig.responsiveSize(12)
            anchors.centerIn: parent
        }

        background: Rectangle {
            radius: 20
            color: "#2269EE"
            border.color: "#5EAAFC"
            border.width: ApplicationConfig.responsiveSize(4)
            visible: tabButton.checked
        }
    }

    TabBar {
        id: tabBar

        readonly property real tabMinimumWidth: Math.ceil(ApplicationConfig.responsiveSize(415))
        implicitWidth: 3 * tabMinimumWidth // space for showing 3 buttons

        contentWidth: ApplicationConfig.responsiveSize(1760)
        contentHeight: ApplicationConfig.responsiveSize(144)
        clip: true

        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            leftMargin: accessoryView.horizontalPaddings
            rightMargin: accessoryView.horizontalPaddings
            topMargin: ApplicationConfig.responsiveSize(120)
        }

        background: Rectangle {
            radius: 20
            color: "white"
            border.width: 2
            border.color: "#D7D6E1"
        }

        AccessoryTabButton {
            id: headwearTabButton
            icon.source: "icons/headwear.svg"
            text: qsTr("Headwear")
            anchors.left: parent.left
        }

        AccessoryTabButton {
            id: eyewearTabButton
            icon.source: "icons/eyewear.svg"
            text: qsTr("Eyewear")
            anchors.left: headwearTabButton.right
        }

        AccessoryTabButton {
            id: eyesTabButton
            icon.source: "icons/eyes.svg"
            text: qsTr("Eyes")
            anchors.left: eyewearTabButton.right
        }

        AccessoryTabButton {
            id: itemsTabButton
            icon.source: "icons/items.svg"
            text: qsTr("Items")
            anchors.left: eyesTabButton.right
        }

        AccessoryTabButton {
            id: nameTabButton
            icon.source: "icons/names.svg"
            text: qsTr("Name")
            anchors.left: itemsTabButton.right
        }
    }

    SortFilterProxyModel {
        id: groupFilterProxyModel
        property string groupFilter: AccessoryModelData.groups()[tabBar.currentIndex] ?? ""
        onGroupFilterChanged: {
            invalidate()
            listView.positionViewAtBeginning()
        }
        filters: [
            FunctionFilter {
                component RoleData: QtObject { property string group }
                function filter(data: RoleData) : bool {
                    return (data.group === groupFilterProxyModel.groupFilter)
                }
            }
        ]
    }

    ListView {
        id: listView

        readonly property real delegateWidth: ApplicationConfig.responsiveSize(560)
        readonly property real delegateHeight: ApplicationConfig.responsiveSize(820)

        implicitWidth: 2 * delegateWidth + spacing  // space for showing 2 items
        implicitHeight: delegateHeight
        visible: tabBar.currentIndex !== 4
        anchors {
            top: tabBar.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            leftMargin: accessoryView.horizontalPaddings
            rightMargin: accessoryView.horizontalPaddings
            bottomMargin: ApplicationConfig.responsiveSize(80)
            topMargin: ApplicationConfig.responsiveSize(80)
        }

        interactive: tabBar.currentIndex !== 4
        orientation: ListView.Horizontal
        boundsBehavior: Flickable.StopAtBounds
        snapMode: ListView.SnapOneItem
        spacing: ApplicationConfig.responsiveSize(64)
        clip: true

        model: groupFilterProxyModel

        function resetAll(group :string) {
            // Single-selection-per-group is now enforced by Python;
            // nothing extra needed here
        }

        delegate: CustomizationCard {
            required property var model
            required property string group
            required property string name
            required property url image
            required property string color
            required property string key
            required selected
            required property int new_price
            required property int old_price
            required property real model_rating
            newPrice: new_price
            oldPrice: old_price
            modelRating: model_rating

            // Resolve the absolute index in the full model so
            // Python receives an index it can use into its internal list.
            required property int index

            function absoluteIndex() : int {
                return groupFilterProxyModel.mapToSource(
                    groupFilterProxyModel.index(index, 0)).row
            }

            implicitWidth: ListView.view.delegateWidth
            implicitHeight: ListView.view.delegateHeight
            anchors.verticalCenter: ListView.view.contentItem.verticalCenter

            cardName: name
            cardImageSource: Qt.resolvedUrl(image)
            selectedColorName: color
            isExclusive: tabBar.currentItem === eyesTabButton

            onChooseRequested: {
                AccessoryModelData.select_accessory(absoluteIndex(), group)
            }

            onRemoveRequested: {
                if (isExclusive) {
                    console.warn("No eyes is selected")
                    return
                }
                AccessoryModelData.deselect_accessory(absoluteIndex())
            }

            onColorChosen: (colorName) => AccessoryModelData.set_color(absoluteIndex(), colorName)
        }
    }

    NameTumbler {
        id: nameTumbler
        visible: tabBar.currentIndex === 4
        anchors {
            top: tabBar.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            leftMargin: accessoryView.horizontalPaddings
            rightMargin: accessoryView.horizontalPaddings
        }
    }
}
