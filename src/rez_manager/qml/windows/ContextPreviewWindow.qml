import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."
import "../components"

// Context preview window — read-only inspection of a resolved context.
// Shows: tools, resolved package list, environment variables.
Window {
    id: root
    title: "Preview — " + contextName_
    width:  820
    height: 640
    color:  Style.bg
    flags:  Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    property string contextName_: "Maya 2024 Base"
    property string projectName_: "VFX Pipeline"


    // ── Dummy resolved data ────────────────────────────────────
    readonly property var toolsList: [
        "maya", "mayapy", "mayabatch",
        "mtoa_render", "usd_view", "usdcat",
        "python3", "pip3"
    ]

    readonly property var resolvedPkgs: [
        { name: "maya",    version: "2024.0.2" },
        { name: "python",  version: "3.11.5"   },
        { name: "mtoa",    version: "5.3.4.1"  },
        { name: "usd",     version: "23.11.1"  },
        { name: "openexr", version: "3.1.10"   },
        { name: "boost",   version: "1.76.0"   },
        { name: "tbb",     version: "2021.8.0" }
    ]

    readonly property var envVars: [
        { name: "MAYA_LOCATION",   value: "/packages/maya/2024.0.2"                              },
        { name: "MAYA_VERSION",    value: "2024"                                                  },
        { name: "PYTHONPATH",      value: "/packages/maya/2024.0.2/lib/python3.11:/packages/mtoa/5.3.4.1/lib/python3.11" },
        { name: "MTOA_HOME",       value: "/packages/mtoa/5.3.4.1"                               },
        { name: "USD_INSTALL_ROOT",value: "/packages/usd/23.11.1"                                },
        { name: "PATH",            value: "/packages/maya/2024.0.2/bin:/packages/python/3.11.5/bin:/usr/bin" },
        { name: "LD_LIBRARY_PATH", value: "/packages/maya/2024.0.2/lib:/packages/openexr/3.1.10/lib" },
        { name: "MAYA_PLUG_IN_PATH",value: "/packages/mtoa/5.3.4.1/plug-ins"                    },
        { name: "OCIO",            value: "/packages/maya/2024.0.2/resources/ACES_1.2/config.ocio" }
    ]

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Title bar ─────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 56
            color:  Style.surface
            ColumnLayout {
                anchors { fill: parent; leftMargin: Style.xl; rightMargin: Style.xl }
                spacing: 2
                Item { Layout.fillHeight: true }
                RowLayout {
                    Text {
                        text:           root.projectName_ + "  /  " + root.contextName_
                        color:          Style.textPrimary
                        font.pixelSize: Style.fontLg
                        font.bold:      true
                    }
                    Item { Layout.fillWidth: true }
                    Badge { text: "Resolved"; badgeColor: Style.success }
                    Item { width: Style.sm }
                    Rectangle {
                        width: 26; height: 26; radius: 13
                        color: closeHov_.containsMouse ? Style.border : "transparent"
                        Text { anchors.centerIn: parent; text: "✕"; color: Style.textSecondary; font.pixelSize: Style.fontMd }
                        MouseArea {
                            id: closeHov_; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: root.close()
                        }
                    }
                }
                Item { Layout.fillHeight: true }
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Style.border }
        }

        // ── Tab bar ───────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 42
            color:  Style.surface

            TabBar {
                id: tabBar_
                anchors.fill: parent
                background: Rectangle { color: "transparent" }

                Repeater {
                    model: ["Tools", "Packages", "Environment"]
                    TabButton {
                        text: modelData
                        width: implicitWidth + 32
                        background: Rectangle {
                            color: "transparent"
                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width; height: 2
                                color: parent.parent.checked ? Style.accent : "transparent"
                                Behavior on color { ColorAnimation { duration: 100 } }
                            }
                        }
                        contentItem: Text {
                            text:            parent.text
                            color:           parent.checked ? Style.accent : Style.textSecondary
                            font.pixelSize:  Style.fontMd
                            font.bold:       parent.checked
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment:   Text.AlignVCenter
                            Behavior on color { ColorAnimation { duration: 100 } }
                        }
                    }
                }
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Style.border }
        }

        // ── Tab content ───────────────────────────────────────
        StackLayout {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            currentIndex: tabBar_.currentIndex

            // ── Tab 0: Tools ──────────────────────────────────
            ScrollView {
                clip: true
                Flow {
                    width: root.width - Style.xl * 2
                    anchors.margins: Style.xl
                    x: Style.xl; y: Style.xl
                    spacing: Style.sm

                    Repeater {
                        model: root.toolsList
                        Rectangle {
                            height: 36; width: toolName_.implicitWidth + 24
                            radius: Style.radiusSm
                            color:  Style.card
                            border.width: 1; border.color: Style.border

                            Row {
                                anchors.centerIn: parent
                                spacing: 8
                                Text { text: "⚙"; color: Style.accent;        font.pixelSize: Style.fontSm; anchors.verticalCenter: parent.verticalCenter }
                                Text {
                                    id: toolName_
                                    text:           modelData
                                    color:          Style.textPrimary
                                    font.pixelSize: Style.fontMd
                                    font.family:    "Consolas, Courier New, monospace"
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                        }
                    }
                }
            }

            // ── Tab 1: Packages ───────────────────────────────
            ScrollView {
                clip: true
                ColumnLayout {
                    width: root.width - Style.xl * 2
                    x: Style.xl; y: Style.xl
                    spacing: 2

                    Repeater {
                        model: root.resolvedPkgs
                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Style.radiusSm
                            color:  pkgHov_.containsMouse ? Style.card : "transparent"
                            Behavior on color { ColorAnimation { duration: 80 } }

                            RowLayout {
                                anchors { fill: parent; leftMargin: Style.md; rightMargin: Style.md }
                                spacing: Style.lg

                                Rectangle { width: 8; height: 8; radius: 4; color: Style.success; Layout.alignment: Qt.AlignVCenter }

                                Text {
                                    text:           modelData.name
                                    color:          Style.textPrimary
                                    font.pixelSize: Style.fontMd
                                    font.family:    "Consolas, Courier New, monospace"
                                    font.bold:      true
                                    Layout.preferredWidth: 160
                                }
                                Text {
                                    text:           modelData.version
                                    color:          Style.textSecondary
                                    font.pixelSize: Style.fontMd
                                    font.family:    "Consolas, Courier New, monospace"
                                }
                                Item { Layout.fillWidth: true }
                            }
                            MouseArea { id: pkgHov_; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                        }
                    }
                }
            }

            // ── Tab 2: Environment ────────────────────────────
            ScrollView {
                clip: true
                ColumnLayout {
                    width: root.width - Style.xl * 2
                    x: Style.xl; y: Style.xl
                    spacing: 2

                    Repeater {
                        model: root.envVars
                        Rectangle {
                            Layout.fillWidth: true
                            height: 42
                            radius: Style.radiusSm
                            color:  envHov_.containsMouse ? Style.card : "transparent"
                            Behavior on color { ColorAnimation { duration: 80 } }

                            RowLayout {
                                anchors { fill: parent; leftMargin: Style.md; rightMargin: Style.md }
                                spacing: Style.lg

                                Text {
                                    text:           modelData.name
                                    color:          Style.accent
                                    font.pixelSize: Style.fontSm
                                    font.family:    "Consolas, Courier New, monospace"
                                    font.bold:      true
                                    Layout.preferredWidth: 200
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text:           modelData.value
                                    color:          Style.textSecondary
                                    font.pixelSize: Style.fontSm
                                    font.family:    "Consolas, Courier New, monospace"
                                    elide:          Text.ElideRight
                                }
                            }
                            MouseArea { id: envHov_; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                        }
                    }
                }
            }
        }
    }
}
