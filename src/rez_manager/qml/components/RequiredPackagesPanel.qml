pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property var packagesModel: null
    property int selectedRow: -1

    signal removeRequested(int index)
    signal packageSelected(int index)

    color: Style.surface

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "transparent"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: Style.md
                anchors.verticalCenter: parent.verticalCenter
                text: "Required Packages"
                color: Style.textSecondary
                font.pixelSize: Style.fontSm
                font.bold: true
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.packagesModel
            clip: true

            ScrollIndicator.vertical: ScrollIndicator {}

            delegate: Rectangle {
                id: requestDelegate_
                required property int index
                required property string pkgName
                required property string displayVersion

                width: ListView.view.width
                height: 46
                color: requestDelegate_.index === root.selectedRow
                    ? Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.12)
                    : (rowHover_.hovered ? Style.elevated : "transparent")

                Behavior on color {
                    ColorAnimation { duration: 80 }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Style.md
                    anchors.rightMargin: Style.sm
                    spacing: Style.sm

                    Rectangle {
                        width: 6
                        height: 6
                        radius: 3
                        color: Style.accent
                        Layout.alignment: Qt.AlignVCenter
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1

                        Text {
                            text: pkgName
                            color: Style.textPrimary
                            font.pixelSize: Style.fontMd
                            font.bold: true
                            elide: Text.ElideRight
                        }

                        Text {
                            text: displayVersion
                            color: Style.textSecondary
                            font.pixelSize: Style.fontXs
                            font.family: "Consolas, Courier New, monospace"
                            elide: Text.ElideRight
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        id: removeButton_
                        Layout.alignment: Qt.AlignVCenter
                        width: 24
                        height: 24
                        radius: Style.radiusSm
                        color: removeTap_.pressed
                            ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.20)
                            : removeHover_.hovered
                                ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.14)
                                : "transparent"
                        border.width: 1
                        border.color: removeHover_.hovered
                            ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.35)
                            : Style.border

                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: Style.error
                            font.pixelSize: Style.fontSm
                            font.bold: true
                        }

                        HoverHandler {
                            id: removeHover_
                            cursorShape: Qt.PointingHandCursor
                        }

                        TapHandler {
                            id: removeTap_
                            acceptedButtons: Qt.LeftButton
                            onTapped: root.removeRequested(index)
                        }
                    }
                }

                HoverHandler {
                    id: rowHover_
                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onTapped: root.packageSelected(requestDelegate_.index)
                }
            }
        }
    }
}
