pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

// Settings dialog — configure repositories and contexts location.
Dialog {
    id: root
    title: "Settings"
    modal: true
    width: 620
    height: Math.max(480, implicitHeight)
    padding: Style.xl
    standardButtons: Dialog.Save | Dialog.Cancel
    onAccepted: root.close()
    onRejected: root.close()

    contentItem: ScrollView {
        clip: true
        ColumnLayout {
            width: root.width - 48
            spacing: Style.xl

            // ── Package Repositories ───────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Style.sm

                Text {
                    text: "Package Repositories"
                    color: Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold: true
                }
                Text {
                    text: "Each folder is treated as a named package group."
                    color: Style.textSecondary
                    font.pixelSize: Style.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }

                // Repo list
                Rectangle {
                    Layout.fillWidth: true
                    height: repoCol_.implicitHeight + Style.md
                    radius: Style.radius
                    color: Style.surface
                    border.width: 1
                    border.color: Style.border

                    ColumnLayout {
                        id: repoCol_
                        anchors {
                            fill: parent
                            margins: Style.sm
                        }
                        spacing: 2

                        Repeater {
                            model: ["/packages/maya", "/packages/houdini", "/packages/base"]
                            delegate: Rectangle {
                                id: repoRow_
                                required property string modelData
                                required property int index
                                Layout.fillWidth: true
                                height: 38
                                radius: Style.radiusSm
                                color: repoHover_.hovered ? Style.elevated : "transparent"
                                Behavior on color {
                                    ColorAnimation {
                                        duration: 80
                                    }
                                }

                                RowLayout {
                                    anchors {
                                        fill: parent
                                        leftMargin: Style.md
                                        rightMargin: Style.sm
                                    }
                                    spacing: Style.sm
                                    Rectangle {
                                        width: 6
                                        height: 6
                                        radius: 3
                                        color: Style.accent
                                        Layout.alignment: Qt.AlignVCenter
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: repoRow_.modelData
                                        color: Style.textPrimary
                                        font.pixelSize: Style.fontMd
                                        font.family: "Consolas, Courier New, monospace"
                                        elide: Text.ElideLeft
                                    }
                                    CardButton {
                                        glyph: "✕"
                                        danger: true
                                    }
                                }
                                HoverHandler {
                                    id: repoHover_
                                }
                            }
                        }
                    }
                }

                // Add repo row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.sm
                    TextField {
                        Layout.fillWidth: true
                        text: "/packages/new"
                        placeholderText: "Repository path"
                    }
                    CardButton {
                        glyph: "+"
                        label: "Add"
                        accent: true
                    }
                }
            }

            // ── Contexts Location ──────────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Style.sm

                Text {
                    text: "Contexts Location"
                    color: Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold: true
                }
                Text {
                    text: "Root directory where project/context data is stored on disk."
                    color: Style.textSecondary
                    font.pixelSize: Style.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.sm
                    TextField {
                        Layout.fillWidth: true
                        text: "/home/user/rez-contexts"
                    }
                    CardButton {
                        label: "Browse…"
                    }
                }
            }
        }
    }
}
