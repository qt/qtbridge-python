// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import QtQuick
import QtQuick.Controls
import backend 1.0

ApplicationWindow {
    visible: true
    width: 400
    height: 300

    ListView {
        anchors.fill: parent
        model: String_model
        delegate: Text { text: modelData }
    }
}
