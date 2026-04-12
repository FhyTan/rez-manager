pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels
import ".."
import "../components"

// Context preview window — read-only inspection of a resolved context.
// Shows: environment variables and resolved package list.
Window {
    id: root
    title: "Preview — " + contextName_
    width: 820
    height: 640
    color: Style.bg
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

    property string contextName_: "Maya 2024 Base"
    property string projectName_: "VFX Pipeline"
    property int contextMenuRow_: -1
    property int hoveredEnvRow_: -1

    // ── Dummy resolved data ────────────────────────────────────
    readonly property var resolvedPkgs: [
        {
            name: "maya",
            version: "2024.0.2"
        },
        {
            name: "python",
            version: "3.11.5"
        },
        {
            name: "mtoa",
            version: "5.3.4.1"
        },
        {
            name: "usd",
            version: "23.11.1"
        },
        {
            name: "openexr",
            version: "3.1.10"
        },
        {
            name: "boost",
            version: "1.76.0"
        },
        {
            name: "tbb",
            version: "2021.8.0"
        }
    ]

    readonly property var envVars: [
        {
            name: "MAYA_LOCATION",
            value: "/packages/maya/2024.0.2"
        },
        {
            name: "MAYA_VERSION",
            value: "2024"
        },
        {
            name: "PYTHONPATH",
            value: "/packages/maya/2024.0.2/lib/python3.11;/packages/mtoa/5.3.4.1/lib/python3.11"
        },
        {
            name: "MTOA_HOME",
            value: "/packages/mtoa/5.3.4.1"
        },
        {
            name: "USD_INSTALL_ROOT",
            value: "/packages/usd/23.11.1"
        },
        {
            name: "PATH",
            value: "/packages/maya/2024.0.2/bin;/packages/python/3.11.5/bin;/usr/bin"
        },
        {
            name: "LD_LIBRARY_PATH",
            value: "/packages/maya/2024.0.2/lib;/packages/openexr/3.1.10/lib"
        },
        {
            name: "MAYA_PLUG_IN_PATH",
            value: "/packages/mtoa/5.3.4.1/plug-ins"
        },
        {
            name: "OCIO",
            value: "/packages/maya/2024.0.2/resources/ACES_1.2/config.ocio"
        }
    ]

    readonly property var contextMenuEntry_: contextMenuRow_ >= 0 && contextMenuRow_ < envVars.length ? envVars[contextMenuRow_] : null

    function formattedEnvValue(rawValue) {
        const value = String(rawValue ?? "");
        if (value.indexOf(";") >= 0)
            return value.replace(/;/g, "\n");
        return value;
    }

    function envRowHeight(rawValue) {
        const lineCount = formattedEnvValue(rawValue).split("\n").length;
        return Math.max(42, 16 + lineCount * 18);
    }

    function copyText(text) {
        clipboardProxy_.text = text;
        clipboardProxy_.selectAll();
        clipboardProxy_.copy();
        clipboardProxy_.deselect();
    }

    function openContextMenu(row, item, point) {
        contextMenuRow_ = row;
        contextMenu_.popup(item, point.x, point.y);
    }

    TextEdit {
        id: clipboardProxy_
        visible: false
    }

    TableModel {
        id: envModel_
        TableModelColumn {
            display: "name"
        }
        TableModelColumn {
            display: "value"
        }
        rows: root.envVars
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Title bar ─────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 56
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
                        text: root.projectName_ + "  /  " + root.contextName_
                        color: Style.textPrimary
                        font.pixelSize: Style.fontLg
                        font.bold: true
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Badge {
                        text: "Resolved"
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

        // ── Tab bar ───────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 42
            color: Style.surface

            TabBar {
                id: tabBar_
                contentHeight: parent.height

                Repeater {
                    model: ["Environment", "Packages"]
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

        // ── Tab content ───────────────────────────────────────
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar_.currentIndex

            // ── Tab 0: Environment ────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                TableView {
                    id: envTable_
                    anchors.fill: parent
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    columnSpacing: 0
                    rowSpacing: 1
                    model: envModel_

                    columnWidthProvider: function (column) {
                        if (column === 0)
                            return 220;
                        return Math.max(320, envTable_.width - 221);
                    }
                    rowHeightProvider: function (row) {
                        return root.envRowHeight(root.envVars[row].value);
                    }

                    delegate: Rectangle {
                        id: cellDelegate_
                        required property bool current
                        required property bool selected
                        required property int row
                        required property int column
                        required property var display

                        color: root.hoveredEnvRow_ === cellDelegate_.row ? Style.cardHover : cellDelegate_.row % 2 === 0 ? Style.surface : Style.bg

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: Style.md
                            anchors.rightMargin: Style.md
                            anchors.topMargin: Style.sm
                            anchors.bottomMargin: Style.sm
                            verticalAlignment: Text.AlignVCenter
                            text: cellDelegate_.column === 0 ? cellDelegate_.display : root.formattedEnvValue(cellDelegate_.display)
                            color: cellDelegate_.column === 0 ? Style.accent : Style.textPrimary
                            font.pixelSize: Style.fontSm
                            font.family: "Consolas, Courier New, monospace"
                            font.bold: cellDelegate_.column === 0
                            wrapMode: Text.Wrap
                        }

                        HoverHandler {
                            cursorShape: Qt.PointingHandCursor
                            onHoveredChanged: {
                                if (hovered)
                                    root.hoveredEnvRow_ = cellDelegate_.row;
                                else if (root.hoveredEnvRow_ === cellDelegate_.row)
                                    root.hoveredEnvRow_ = -1;
                            }
                        }
                        TapHandler {
                            acceptedButtons: Qt.RightButton
                            onTapped: function (eventPoint) {
                                root.openContextMenu(cellDelegate_.row, cellDelegate_, eventPoint.position);
                            }
                        }
                    }

                    ScrollBar.vertical: ScrollBar {}
                    ScrollBar.horizontal: ScrollBar {}
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

            // ── Tab 1: Packages ───────────────────────────────
            ScrollView {
                clip: true
                ColumnLayout {
                    width: root.width - Style.xl * 2
                    x: Style.xl
                    y: Style.xl
                    spacing: 2

                    Repeater {
                        model: root.resolvedPkgs
                        Rectangle {
                            id: pkgDelegate_
                            required property var modelData
                            Layout.fillWidth: true
                            height: 40
                            radius: Style.radiusSm
                            color: pkgHov_.hovered ? Style.card : "transparent"
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
                                    width: 8
                                    height: 8
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
                                    text: pkgDelegate_.modelData.version
                                    color: Style.textSecondary
                                    font.pixelSize: Style.fontMd
                                    font.family: "Consolas, Courier New, monospace"
                                }
                                Item {
                                    Layout.fillWidth: true
                                }
                            }
                            HoverHandler {
                                id: pkgHov_
                            }
                        }
                    }
                }
            }
        }
    }
}
