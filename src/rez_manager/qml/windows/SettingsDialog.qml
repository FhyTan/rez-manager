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
        color:        s_.elevated
        radius:       s_.radiusLg
        border.width: 1
        border.color: s_.borderBright
    }

    header: Rectangle {
        height: 56
        color:  "transparent"
        RowLayout {
            anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.lg }
            Text {
                text:           "Settings"
                color:          s_.textPrimary
                font.pixelSize: s_.fontXl
                font.bold:      true
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                width: 28; height: 28; radius: 14
                color: closeHover_.containsMouse ? s_.border : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "✕"; color: s_.textSecondary; font.pixelSize: s_.fontMd
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
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
    }

    footer: Rectangle {
        height: 56
        color:  "transparent"
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: s_.border }
        RowLayout {
            anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.xl }
            Item { Layout.fillWidth: true }
            CardButton { label: "Cancel"; onClicked: root.close() }
            Item { width: s_.sm }
            CardButton { label: "Save"; accent: true; onClicked: root.close() }
        }
    }

    Style { id: s_ }

    contentItem: ScrollView {
        clip: true
        ColumnLayout {
            width: root.width - 48
            spacing: s_.xl

            // ── Package Repositories ───────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                spacing: s_.sm

                Text {
                    text:           "Package Repositories"
                    color:          s_.textPrimary
                    font.pixelSize: s_.fontLg
                    font.bold:      true
                }
                Text {
                    text:           "Each folder is treated as a named package group."
                    color:          s_.textSecondary
                    font.pixelSize: s_.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }

                // Repo list
                Rectangle {
                    Layout.fillWidth: true
                    height:       repoCol_.implicitHeight + s_.md
                    radius:       s_.radius
                    color:        s_.surface
                    border.width: 1
                    border.color: s_.border

                    ColumnLayout {
                        id: repoCol_
                        anchors { fill: parent; margins: s_.sm }
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
                                radius:       s_.radiusSm
                                color:        repoHover_.containsMouse ? s_.elevated : "transparent"
                                Behavior on color { ColorAnimation { duration: 80 } }

                                RowLayout {
                                    anchors { fill: parent; leftMargin: s_.md; rightMargin: s_.sm }
                                    spacing: s_.sm
                                    Rectangle {
                                        width: 6; height: 6; radius: 3; color: s_.accent
                                        Layout.alignment: Qt.AlignVCenter
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text:           modelData
                                        color:          s_.textPrimary
                                        font.pixelSize: s_.fontMd
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
                    spacing: s_.sm
                    Rectangle {
                        Layout.fillWidth: true
                        height: 36; radius: s_.radiusSm
                        color: s_.surface; border.width: 1; border.color: s_.border
                        TextInput {
                            anchors.left: parent.left; anchors.right: parent.right
                            anchors.leftMargin: s_.md; anchors.rightMargin: s_.md
                            anchors.verticalCenter: parent.verticalCenter
                            text:            "/packages/new"
                            color:           s_.textSecondary
                            font.pixelSize:  s_.fontMd
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
                spacing: s_.sm

                Text {
                    text:           "Contexts Location"
                    color:          s_.textPrimary
                    font.pixelSize: s_.fontLg
                    font.bold:      true
                }
                Text {
                    text:           "Root directory where project/context data is stored on disk."
                    color:          s_.textSecondary
                    font.pixelSize: s_.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: s_.sm
                    Rectangle {
                        Layout.fillWidth: true
                        height: 36; radius: s_.radiusSm
                        color: s_.surface; border.width: 1; border.color: s_.border
                        TextInput {
                            anchors.left: parent.left; anchors.right: parent.right
                            anchors.leftMargin: s_.md; anchors.rightMargin: s_.md
                            anchors.verticalCenter: parent.verticalCenter
                            text:           "/home/user/rez-contexts"
                            color:          s_.textPrimary
                            font.pixelSize: s_.fontMd
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
