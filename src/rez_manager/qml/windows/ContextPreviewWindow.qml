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

    property ContextPreviewController contextPreviewController: null
    property var contextMenuEntry_: null

    function formattedEnvValue(variableName, rawValue) {
        const value = String(rawValue ?? "");
        if (!root.contextPreviewController)
            return value;
        const separator = String(root.contextPreviewController.pathSeparator ?? "");
        if (separator.length === 1 && value.indexOf(separator) >= 0)
            return value.split(separator).join("\n");
        return value;
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
                        text: qsTr("Resolved")
                        badgeColor: Style.success
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
                id: environmentScroll_
                clip: true
                leftPadding: Style.xl
                topPadding: Style.xl
                rightPadding: Style.xl
                bottomPadding: Style.xl

                ColumnLayout {
                    width: environmentScroll_.availableWidth
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

                                TableView {
                                    id: sectionTable_
                                    visible: sectionDelegate_.modelData.rowCount > 0
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: contentHeight
                                    implicitHeight: contentHeight
                                    clip: true
                                    interactive: false
                                    boundsBehavior: Flickable.StopAtBounds
                                    columnSpacing: 0
                                    rowSpacing: 0
                                    model: sectionDelegate_.modelData.tableModel

                                    property real keyColumnWidth: Math.min(240, Math.max(180, width * 0.32))
                                    property int hoveredRow: -1

                                    columnWidthProvider: function (column) {
                                        if (column === 0)
                                            return sectionTable_.keyColumnWidth;
                                        return Math.max(220, sectionTable_.width - sectionTable_.keyColumnWidth);
                                    }

                                    delegate: Rectangle {
                                        id: cellDelegate_
                                        required property int row
                                        required property int column
                                        readonly property real horizontalPadding: Style.md * 2
                                        readonly property real verticalPadding: Style.sm * 2

                                        property var rowData: sectionDelegate_.modelData.tableModel.rowData(row)
                                        implicitWidth: sectionTable_.columnWidthProvider(cellDelegate_.column)
                                        implicitHeight: Math.max(42, Math.ceil(Math.max(keyMeasure_.implicitHeight, valueMeasure_.implicitHeight)) + cellDelegate_.verticalPadding)
                                        color: sectionTable_.hoveredRow === cellDelegate_.row ? Style.cardHover : Style.surface

                                        Rectangle {
                                            anchors {
                                                left: parent.left
                                                right: parent.right
                                                bottom: parent.bottom
                                            }
                                            height: 1
                                            color: Style.border
                                        }

                                        Text {
                                            anchors {
                                                fill: parent
                                                leftMargin: Style.md
                                                rightMargin: Style.md
                                                topMargin: Style.sm
                                                bottomMargin: Style.sm
                                            }
                                            text: cellDelegate_.column === 0 ? cellDelegate_.rowData.name : root.formattedEnvValue(cellDelegate_.rowData.name, cellDelegate_.rowData.value)
                                            color: cellDelegate_.column === 0 ? Style.accent : Style.textPrimary
                                            font.pixelSize: Style.fontSm
                                            font.family: "Consolas, Courier New, monospace"
                                            font.bold: cellDelegate_.column === 0
                                            wrapMode: Text.Wrap
                                            verticalAlignment: Text.AlignVCenter
                                        }

                                        Text {
                                            id: keyMeasure_
                                            visible: false
                                            width: sectionTable_.columnWidthProvider(0) - cellDelegate_.horizontalPadding
                                            text: cellDelegate_.rowData.name
                                            font.pixelSize: Style.fontSm
                                            font.family: "Consolas, Courier New, monospace"
                                            font.bold: true
                                            wrapMode: Text.Wrap
                                        }

                                        Text {
                                            id: valueMeasure_
                                            visible: false
                                            width: sectionTable_.columnWidthProvider(1) - cellDelegate_.horizontalPadding
                                            text: root.formattedEnvValue(cellDelegate_.rowData.name, cellDelegate_.rowData.value)
                                            font.pixelSize: Style.fontSm
                                            font.family: "Consolas, Courier New, monospace"
                                            wrapMode: Text.Wrap
                                        }

                                        HoverHandler {
                                            id: cellHover_
                                            cursorShape: Qt.PointingHandCursor
                                            onHoveredChanged: {
                                                if (hovered)
                                                    sectionTable_.hoveredRow = cellDelegate_.row;
                                                else if (sectionTable_.hoveredRow === cellDelegate_.row)
                                                    sectionTable_.hoveredRow = -1;
                                            }
                                        }

                                        TapHandler {
                                            gesturePolicy: TapHandler.WithinBounds
                                            acceptedButtons: Qt.RightButton
                                            onTapped: function (eventPoint) {
                                                root.openContextMenu(cellDelegate_.rowData, cellDelegate_, eventPoint.position);
                                            }
                                        }
                                    }
                                }

                                Text {
                                    visible: sectionDelegate_.modelData.rowCount === 0
                                    text: qsTr("No variables in this section.")
                                    color: Style.textSecondary
                                    font.pixelSize: Style.fontSm
                                }
                            }
                        }
                    }

                    Rectangle {
                        visible: root.contextPreviewController && !root.contextPreviewController.hasData
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
                id: packagesScroll_
                clip: true
                leftPadding: Style.xl
                topPadding: Style.xl
                rightPadding: Style.xl
                bottomPadding: Style.xl

                ColumnLayout {
                    width: packagesScroll_.availableWidth
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
                        visible: root.contextPreviewController && root.contextPreviewController.resolvedPackages.length === 0
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
