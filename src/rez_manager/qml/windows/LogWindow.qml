pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager
import ".."
import "../components"

Window {
    id: root
    title: qsTr("Application Logs")
    width: 920
    height: 640
    color: Style.bg
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

    property LogViewerController logViewerController: null

    function refresh() {
        if (root.logViewerController)
            root.logViewerController.refresh();
    }

    function scrollToEnd() {
        logFlickable_.contentY = Math.max(0, logFlickable_.contentHeight - logFlickable_.height);
        logFlickable_.contentX = 0;
    }

    onVisibleChanged: {
        if (visible) {
            refresh();
            Qt.callLater(root.scrollToEnd);
        }
    }

    Connections {
        target: root.logViewerController
        function onStateChanged() {
            Qt.callLater(root.scrollToEnd);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 56
            color: Style.surface

            RowLayout {
                anchors {
                    fill: parent
                    leftMargin: Style.xl
                    rightMargin: Style.xl
                }

                Text {
                    text: qsTr("Application Logs")
                    color: Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold: true
                }

                Badge {
                    visible: root.logViewerController && root.logViewerController.isTruncated
                    text: root.logViewerController ? qsTr("Last %1 lines").arg(root.logViewerController.tailLineCount) : ""
                    badgeColor: Style.accent
                }

                Item {
                    Layout.fillWidth: true
                }

                CardButton {
                    glyph: "↻"
                    label: qsTr("Refresh")
                    onClicked: root.refresh()
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
            implicitHeight: pathLayout_.implicitHeight + Style.md * 2
            color: Style.surface

            ColumnLayout {
                id: pathLayout_
                anchors {
                    fill: parent
                    leftMargin: Style.xl
                    rightMargin: Style.xl
                    topMargin: Style.md
                    bottomMargin: Style.md
                }
                spacing: Style.xs

                Text {
                    text: qsTr("Log file")
                    color: Style.textSecondary
                    font.pixelSize: Style.fontSm
                }

                Text {
                    text: root.logViewerController ? root.logViewerController.logUrl : ""
                    color: pathHover_.hovered ? Style.accentHover : Style.accent
                    font.pixelSize: Style.fontSm
                    wrapMode: Text.WrapAnywhere

                    HoverHandler {
                        id: pathHover_
                        cursorShape: Qt.PointingHandCursor
                    }

                    TapHandler {
                        gesturePolicy: TapHandler.WithinBounds
                        onTapped: {
                            if (root.logViewerController && root.logViewerController.logUrl.length > 0)
                                Qt.openUrlExternally(root.logViewerController.logUrl);
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

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Style.bg

            ScrollView {
                anchors.fill: parent
                anchors.margins: Style.xl
                clip: true

                Flickable {
                    id: logFlickable_
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    contentWidth: logPanel_.width
                    contentHeight: logPanel_.height

                    Rectangle {
                        id: logPanel_
                        width: Math.max(logFlickable_.width, logText_.implicitWidth + Style.md * 2)
                        height: Math.max(logFlickable_.height, logText_.implicitHeight + Style.md * 2)
                        radius: Style.radius
                        color: Style.surface
                        border.width: 1
                        border.color: Style.border

                        TextEdit {
                            id: logText_
                            anchors.fill: parent
                            anchors.margins: Style.md
                            readOnly: true
                            selectByMouse: true
                            text: root.logViewerController ? (root.logViewerController.loadError.length > 0 ? root.logViewerController.loadError : root.logViewerController.logText) : ""
                            color: root.logViewerController && root.logViewerController.loadError.length > 0 ? Style.error : Style.textPrimary
                            wrapMode: TextEdit.NoWrap
                            font.family: "Cascadia Mono"
                            font.pixelSize: Style.fontSm
                            persistentSelection: true
                        }
                    }
                }
            }
        }
    }
}
