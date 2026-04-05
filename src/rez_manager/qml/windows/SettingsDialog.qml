import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."
import "../components"

// Settings dialog — configure repositories and contexts location.
Dialog {
    id: root
    title: "Settings"
    modal: true
    width:  620
    height: 480

    background: Rectangle {
        color:        Style.elevated
        radius:       Style.radiusLg
        border.width: 1
        border.color: Style.borderBright
    }

    header: Rectangle {
        height: 56
        color:  "transparent"
        RowLayout {
            anchors { fill: parent; leftMargin: Style.xl; rightMargin: Style.lg }
            Text {
                text:           "Settings"
                color:          Style.textPrimary
                font.pixelSize: Style.fontXl
                font.bold:      true
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                width: 28; height: 28; radius: 14
                color: closeHover_.containsMouse ? Style.border : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "✕"; color: Style.textSecondary; font.pixelSize: Style.fontMd
                }
                MouseArea {
                    id: closeHover_
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.close()
                }
            }
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Style.border }
    }

    footer: Rectangle {
        height: 56
        color:  "transparent"
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Style.border }
        RowLayout {
            anchors { fill: parent; leftMargin: Style.xl; rightMargin: Style.xl }
            Item { Layout.fillWidth: true }
            CardButton { label: "Cancel"; onClicked: root.close() }
            Item { width: Style.sm }
            CardButton { label: "Save"; accent: true; onClicked: root.close() }
        }
    }


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
                    text:           "Package Repositories"
                    color:          Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold:      true
                }
                Text {
                    text:           "Each folder is treated as a named package group."
                    color:          Style.textSecondary
                    font.pixelSize: Style.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }

                // Repo list
                Rectangle {
                    Layout.fillWidth: true
                    height:       repoCol_.implicitHeight + Style.md
                    radius:       Style.radius
                    color:        Style.surface
                    border.width: 1
                    border.color: Style.border

                    ColumnLayout {
                        id: repoCol_
                        anchors { fill: parent; margins: Style.sm }
                        spacing: 2

                        Repeater {
                            model: [
                                "/packages/maya",
                                "/packages/houdini",
                                "/packages/base"
                            ]
                            delegate: Rectangle {
                                required property string modelData
                                required property int    index
                                Layout.fillWidth: true
                                height:       38
                                radius:       Style.radiusSm
                                color:        repoHover_.containsMouse ? Style.elevated : "transparent"
                                Behavior on color { ColorAnimation { duration: 80 } }

                                RowLayout {
                                    anchors { fill: parent; leftMargin: Style.md; rightMargin: Style.sm }
                                    spacing: Style.sm
                                    Rectangle {
                                        width: 6; height: 6; radius: 3; color: Style.accent
                                        Layout.alignment: Qt.AlignVCenter
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text:           modelData
                                        color:          Style.textPrimary
                                        font.pixelSize: Style.fontMd
                                        font.family:    "Consolas, Courier New, monospace"
                                        elide:          Text.ElideLeft
                                    }
                                    CardButton { icon: "✕"; danger: true }
                                }
                                MouseArea { id: repoHover_; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                            }
                        }
                    }
                }

                // Add repo row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.sm
                    Rectangle {
                        Layout.fillWidth: true
                        height: 36; radius: Style.radiusSm
                        color: Style.surface; border.width: 1; border.color: Style.border
                        TextInput {
                            anchors.left: parent.left; anchors.right: parent.right
                            anchors.leftMargin: Style.md; anchors.rightMargin: Style.md
                            anchors.verticalCenter: parent.verticalCenter
                            text:            "/packages/new"
                            color:           Style.textSecondary
                            font.pixelSize:  Style.fontMd
                            font.family:     "Consolas, Courier New, monospace"
                            selectByMouse:   true
                        }
                    }
                    CardButton { icon: "+"; label: "Add"; accent: true }
                }
            }

            // ── Contexts Location ──────────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Style.sm

                Text {
                    text:           "Contexts Location"
                    color:          Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold:      true
                }
                Text {
                    text:           "Root directory where project/context data is stored on disk."
                    color:          Style.textSecondary
                    font.pixelSize: Style.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.sm
                    Rectangle {
                        Layout.fillWidth: true
                        height: 36; radius: Style.radiusSm
                        color: Style.surface; border.width: 1; border.color: Style.border
                        TextInput {
                            anchors.left: parent.left; anchors.right: parent.right
                            anchors.leftMargin: Style.md; anchors.rightMargin: Style.md
                            anchors.verticalCenter: parent.verticalCenter
                            text:           "/home/user/rez-contexts"
                            color:          Style.textPrimary
                            font.pixelSize: Style.fontMd
                            font.family:    "Consolas, Courier New, monospace"
                            selectByMouse:  true
                        }
                    }
                    CardButton { label: "Browse…" }
                }
            }
        }
    }
}
