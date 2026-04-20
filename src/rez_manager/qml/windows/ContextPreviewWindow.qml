pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager
import ".."
import "../components"

// Context preview window — read-only inspection of a resolved context.
Window {
    id: root
    title: qsTr("Preview - ") + (root.contextPreviewController ? root.contextPreviewController.contextName : "")
    width: 820
    height: 640
    color: Style.bg
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

    required property ContextPreviewController contextPreviewController
    property var contextMenuEntry_: null

    function isPathListVariable(variableName) {
        const normalizedName = String(variableName ?? "").toUpperCase();
        return normalizedName === "PATH" || normalizedName.endsWith("PATH");
    }

    function formattedEnvValue(variableName, rawValue) {
        const value = String(rawValue ?? "");
        if (!root.contextPreviewController)
            return value;
        if (!isPathListVariable(variableName))
            return value;
        const separator = String(root.contextPreviewController.pathSeparator ?? "");
        if (separator.length === 1 && value.indexOf(separator) >= 0)
            return value.split(separator).join("\n");
        return value;
    }

    function envRowHeight(variableName, rawValue) {
        const lineCount = formattedEnvValue(variableName, rawValue).split("\n").length;
        return Math.max(42, 16 + lineCount * 18);
    }

    function copyText(text) {
        clipboardProxy_.text = text;
        clipboardProxy_.selectAll();
        clipboardProxy_.copy();
        clipboardProxy_.deselect();
    }

    function openContextMenu(entry, item, point) {
        contextMenuEntry_ = entry;
        contextMenu_.popup(item, point.x, point.y);
    }

    TextEdit {
        id: clipboardProxy_
        visible: false
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 56
            color: Style.surface

            ColumnLayout {
                anchors {
                    fill: parent
                    leftMargin: Style.xl
                    rightMargin: Style.xl
                }
                spacing: 2

                Item {
                    Layout.fillHeight: true
                }

                RowLayout {
                    Text {
                        text: root.contextPreviewController ? root.contextPreviewController.projectName + "  /  " + root.contextPreviewController.contextName : ""
                        color: Style.textPrimary
                        font.pixelSize: Style.fontLg
                        font.bold: true
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Badge {
                        text: root.contextPreviewController.isLoading ? qsTr("Loading") : qsTr("Resolved")
                        badgeColor: root.contextPreviewController.isLoading ? Style.warning : Style.success
                    }
                }

                Item {
                    Layout.fillHeight: true
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 42
            color: Style.surface

            TabBar {
                id: tabBar_
                contentHeight: parent.height

                Repeater {
                    model: [qsTr("Environment"), qsTr("Packages")]

                    TabButton {
                        id: tabButton_
                        required property string modelData
                        text: tabButton_.modelData
                        width: implicitWidth + 32
                        height: tabBar_.height
                        topPadding: 0
                        bottomPadding: 0
                        leftPadding: 0
                        rightPadding: 0

                        background: Rectangle {
                            color: "transparent"

                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: 2
                                color: tabButton_.checked ? Style.accent : "transparent"

                                Behavior on color {
                                    ColorAnimation {
                                        duration: 100
                                    }
                                }
                            }
                        }

                        contentItem: Text {
                            anchors.fill: parent
                            text: tabButton_.text
                            color: tabButton_.checked ? Style.accent : Style.textSecondary
                            font.pixelSize: Style.fontMd
                            font.bold: tabButton_.checked
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter

                            Behavior on color {
                                ColorAnimation {
                                    duration: 100
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar_.currentIndex

            ScrollView {
                clip: true

                ColumnLayout {
                    width: root.width - Style.xl * 2
                    x: Style.xl
                    y: Style.xl
                    spacing: Style.lg

                    Repeater {
                        model: root.contextPreviewController ? root.contextPreviewController.environmentSections : []

                        Rectangle {
                            id: sectionDelegate_
                            required property var modelData
                            Layout.fillWidth: true
                            radius: Style.radius
                            color: Style.surface
                            border.width: 1
                            border.color: Style.border
                            implicitHeight: sectionLayout_.implicitHeight + Style.lg * 2

                            ColumnLayout {
                                id: sectionLayout_
                                anchors {
                                    fill: parent
                                    margins: Style.lg
                                }
                                spacing: Style.md

                                Text {
                                    text: sectionDelegate_.modelData.title
                                    color: Style.textPrimary
                                    font.pixelSize: Style.fontLg
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 1
                                    color: Style.border
                                }

                                Repeater {
                                    model: sectionDelegate_.modelData.rows

                                    Rectangle {
                                        id: rowDelegate_
                                        required property int index
                                        required property var modelData
                                        Layout.fillWidth: true
                                        implicitHeight: root.envRowHeight(rowDelegate_.modelData.name, rowDelegate_.modelData.value)
                                        radius: Style.radiusSm
                                        color: rowHover_.hovered ? Style.cardHover : index % 2 === 0 ? Style.surface : Style.bg

                                        RowLayout {
                                            anchors {
                                                fill: parent
                                                leftMargin: Style.md
                                                rightMargin: Style.md
                                                topMargin: Style.sm
                                                bottomMargin: Style.sm
                                            }
                                            spacing: Style.md

                                            Text {
                                                Layout.preferredWidth: 220
                                                text: rowDelegate_.modelData.name
                                                color: Style.accent
                                                font.pixelSize: Style.fontSm
                                                font.family: "Consolas, Courier New, monospace"
                                                font.bold: true
                                                wrapMode: Text.Wrap
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: root.formattedEnvValue(rowDelegate_.modelData.name, rowDelegate_.modelData.value)
                                                color: Style.textPrimary
                                                font.pixelSize: Style.fontSm
                                                font.family: "Consolas, Courier New, monospace"
                                                wrapMode: Text.Wrap
                                            }
                                        }

                                        HoverHandler {
                                            id: rowHover_
                                            cursorShape: Qt.PointingHandCursor
                                        }

                                        TapHandler {
                                            gesturePolicy: TapHandler.WithinBounds
                                            acceptedButtons: Qt.RightButton
                                            onTapped: function (eventPoint) {
                                                root.openContextMenu(rowDelegate_.modelData, rowDelegate_, eventPoint.position);
                                            }
                                        }
                                    }
                                }

                                Text {
                                    visible: sectionDelegate_.modelData.rows.length === 0
                                    text: qsTr("No variables in this section.")
                                    color: Style.textSecondary
                                    font.pixelSize: Style.fontSm
                                }
                            }
                        }
                    }

                    Rectangle {
                        visible: root.contextPreviewController.isLoading
                        Layout.fillWidth: true
                        radius: Style.radius
                        color: Style.surface
                        border.width: 1
                        border.color: Style.border
                        implicitHeight: 120

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: Style.md

                            BusyIndicator {
                                running: true
                            }

                            Text {
                                text: qsTr("Resolving preview...")
                                color: Style.textSecondary
                                font.pixelSize: Style.fontMd
                            }
                        }
                    }

                    Rectangle {
                        visible: !root.contextPreviewController.isLoading && !root.contextPreviewController.hasData
                        Layout.fillWidth: true
                        radius: Style.radius
                        color: Style.surface
                        border.width: 1
                        border.color: Style.border
                        implicitHeight: 120

                        Text {
                            anchors.centerIn: parent
                            text: qsTr("No preview data loaded.")
                            color: Style.textSecondary
                            font.pixelSize: Style.fontMd
                        }
                    }
                }
            }

            ScrollView {
                clip: true

                ColumnLayout {
                    width: root.width - Style.xl * 2
                    x: Style.xl
                    y: Style.xl
                    spacing: 2

                    Repeater {
                        model: root.contextPreviewController ? root.contextPreviewController.resolvedPackages : []

                        Rectangle {
                            id: pkgDelegate_
                            required property var modelData
                            Layout.fillWidth: true
                            height: 40
                            radius: Style.radiusSm
                            color: pkgHover_.hovered ? Style.card : "transparent"

                            Behavior on color {
                                ColorAnimation {
                                    duration: 80
                                }
                            }

                            RowLayout {
                                anchors {
                                    fill: parent
                                    leftMargin: Style.md
                                    rightMargin: Style.md
                                }
                                spacing: Style.lg

                                Rectangle {
                                    implicitWidth: 8
                                    implicitHeight: 8
                                    radius: 4
                                    color: Style.success
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                Text {
                                    text: pkgDelegate_.modelData.name
                                    color: Style.textPrimary
                                    font.pixelSize: Style.fontMd
                                    font.family: "Consolas, Courier New, monospace"
                                    font.bold: true
                                    Layout.preferredWidth: 160
                                }

                                Text {
                                    text: pkgDelegate_.modelData.version.length > 0 ? pkgDelegate_.modelData.version : pkgDelegate_.modelData.label
                                    color: Style.textSecondary
                                    font.pixelSize: Style.fontMd
                                    font.family: "Consolas, Courier New, monospace"
                                }

                                Item {
                                    Layout.fillWidth: true
                                }
                            }

                            HoverHandler {
                                id: pkgHover_
                            }
                        }
                    }

                    Rectangle {
                        visible: root.contextPreviewController.isLoading
                        Layout.fillWidth: true
                        radius: Style.radius
                        color: Style.surface
                        border.width: 1
                        border.color: Style.border
                        implicitHeight: 120

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: Style.md

                            BusyIndicator {
                                running: true
                            }

                            Text {
                                text: qsTr("Resolving packages...")
                                color: Style.textSecondary
                                font.pixelSize: Style.fontMd
                            }
                        }
                    }

                    Rectangle {
                        visible: !root.contextPreviewController.isLoading && root.contextPreviewController.resolvedPackages.length === 0
                        Layout.fillWidth: true
                        radius: Style.radius
                        color: Style.surface
                        border.width: 1
                        border.color: Style.border
                        implicitHeight: 120

                        Text {
                            anchors.centerIn: parent
                            text: qsTr("No packages resolved yet.")
                            color: Style.textSecondary
                            font.pixelSize: Style.fontMd
                        }
                    }
                }
            }
        }
    }

    Menu {
        id: contextMenu_

        MenuItem {
            text: qsTr("Copy key")
            enabled: root.contextMenuEntry_ !== null
            onTriggered: root.copyText(root.contextMenuEntry_.name)
        }

        MenuItem {
            text: qsTr("Copy value")
            enabled: root.contextMenuEntry_ !== null
            onTriggered: root.copyText(root.contextMenuEntry_.value)
        }

        MenuItem {
            text: qsTr("Copy key=value")
            enabled: root.contextMenuEntry_ !== null
            onTriggered: root.copyText(root.contextMenuEntry_.name + "=" + root.contextMenuEntry_.value)
        }
    }
}
