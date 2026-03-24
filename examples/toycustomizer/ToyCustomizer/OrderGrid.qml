// Copyright (C) 2026 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import backend 1.0

Item {
    id: selection

    enum ModelGroup {
        Face,
        Eyeswear,
        Headwear,
        Item,
        Name,
        Toy
    }

    property int totalPrice: OrderData.total_price
    property int toyIndex: -1
    required property var accessoryModel  // kept for API compat; logic is in Python
    property bool wrap: false

    // Trigger Python order calculation whenever toyIndex is set
    onToyIndexChanged: {
        OrderData.toy_index = toyIndex
        OrderData.calculate_order()
    }
    Component.onCompleted: {
        OrderData.toy_index = toyIndex
        OrderData.calculate_order()
    }

    // All slot data comes directly from the Python OrderData singleton.
    component GridOrderItem : OrderItem {
        id: orderItem

        required property int group

        image: {
            switch (group) {
                case OrderGrid.ModelGroup.Toy:     return Qt.url(OrderData.toy_image)
                case OrderGrid.ModelGroup.Face:    return Qt.url(OrderData.face_image)
                case OrderGrid.ModelGroup.Headwear: return Qt.url(OrderData.headwear_image)
                case OrderGrid.ModelGroup.Item:    return Qt.url(OrderData.item_image)
                case OrderGrid.ModelGroup.Eyeswear: return Qt.url(OrderData.eyewear_image)
                default: return Qt.url("")
            }
        }
        name: {
            switch (group) {
                case OrderGrid.ModelGroup.Toy:     return OrderData.toy_name
                case OrderGrid.ModelGroup.Face:    return OrderData.face_name
                case OrderGrid.ModelGroup.Headwear: return OrderData.headwear_name
                case OrderGrid.ModelGroup.Item:    return OrderData.item_name
                case OrderGrid.ModelGroup.Eyeswear: return OrderData.eyewear_name
                case OrderGrid.ModelGroup.Name:    return OrderData.selected_name
                default: return ""
            }
        }
        oldPrice: {
            switch (group) {
                case OrderGrid.ModelGroup.Toy:     return OrderData.toy_old_price
                case OrderGrid.ModelGroup.Face:    return OrderData.face_old_price
                case OrderGrid.ModelGroup.Headwear: return OrderData.headwear_old_price
                case OrderGrid.ModelGroup.Item:    return OrderData.item_old_price
                case OrderGrid.ModelGroup.Eyeswear: return OrderData.eyewear_old_price
                default: return 0
            }
        }
        newPrice: {
            switch (group) {
                case OrderGrid.ModelGroup.Toy:     return OrderData.toy_new_price
                case OrderGrid.ModelGroup.Face:    return OrderData.face_new_price
                case OrderGrid.ModelGroup.Headwear: return OrderData.headwear_new_price
                case OrderGrid.ModelGroup.Item:    return OrderData.item_new_price
                case OrderGrid.ModelGroup.Eyeswear: return OrderData.eyewear_new_price
                default: return 0
            }
        }
        isSelected: {
            switch (group) {
                case OrderGrid.ModelGroup.Toy:     return selection.toyIndex >= 0
                case OrderGrid.ModelGroup.Face:    return OrderData.face_name !== ""
                case OrderGrid.ModelGroup.Headwear: return OrderData.headwear_name !== ""
                case OrderGrid.ModelGroup.Item:    return OrderData.item_name !== ""
                case OrderGrid.ModelGroup.Eyeswear: return OrderData.eyewear_name !== ""
                case OrderGrid.ModelGroup.Name:    return true
                default: return false
            }
        }
        priceVisible: oldPrice > 0
    }

    implicitWidth: orders.implicitWidth

    ToyLabel {
        id: order
        anchors {
            top: parent.top
            left: parent.left
        }
        textStyle: ApplicationConfig.TextStyle.H2_Bold
        text: qsTr("Your order")
    }

    GridLayout {
        id: orders
        anchors {
            top: order.bottom
            bottom: parent.bottom
            left: parent.left
            right: parent.right
            topMargin: ApplicationConfig.responsiveSize(90)
        }
        columns: 2
        columnSpacing: Math.floor(ApplicationConfig.responsiveSize(80))
        rowSpacing: Math.floor(ApplicationConfig.responsiveSize(80))
        uniformCellWidths: true

        GridOrderItem {
            id: toy
            group: OrderGrid.ModelGroup.Toy
            isSelected: true // this should be always true as there is always a toy in an order
            label: "Toy"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: !selection.wrap ? implicitWidth : -1
        }
        GridOrderItem {
            id: face
            group: OrderGrid.ModelGroup.Face
            label: "Face"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: !selection.wrap ? implicitWidth : -1
        }
        GridOrderItem {
            id: headwear
            group: OrderGrid.ModelGroup.Headwear
            label: "HeadWear"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: !selection.wrap ? implicitWidth : -1
        }
        GridOrderItem {
            id: accessory
            group: OrderGrid.ModelGroup.Item
            label: "Accessory"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: !selection.wrap ? implicitWidth : -1
        }
        GridOrderItem {
            id: eyewear
            group: OrderGrid.ModelGroup.Eyeswear
            label: "Eyewear"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: !selection.wrap ? implicitWidth : -1
        }
        GridOrderItem {
            id: name
            group: OrderGrid.ModelGroup.Name
            label: "Name"
            isSelected: true
            priceVisible: false
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: !selection.wrap ? implicitWidth : -1
        }
    }
}
