pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property var repositoryModel: null
    property int selectedRepoIndex: -1
    property int selectedPkgIndex: -1
    property bool isLoading: false

    signal packageSelected(int repoIndex, int pkgIndex)

    color: Style.bg

    function toggleTopLevelRow(treeView, row, repoIndex) {
        if (treeView.isExpanded(row)) {
            treeView.collapse(row);
            return;
        }

        for (let visibleRow = 0; visibleRow < treeView.rows; ++visibleRow) {
            if (visibleRow === row)
                continue;
            if (treeView.depth(visibleRow) === 0 && treeView.isExpanded(visibleRow))
                treeView.collapse(visibleRow);
        }

        treeView.expand(repoIndex);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 40
            color: "transparent"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: Style.md
                anchors.verticalCenter: parent.verticalCenter
                text: "Package Repository"
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

        TreeView {
            id: repositoryTreeView_
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            enabled: !root.isLoading
            opacity: root.isLoading ? 0.45 : 1
            model: root.repositoryModel
            columnWidthProvider: function (column) {
                return width;
            }

            delegate: Rectangle {
                id: delegateRoot_
                required property TreeView treeView
                required property bool expanded
                required property bool hasChildren
                required property int depth
                required property int row
                required property int column
                required property string label
                required property string nodeType
                required property int repoIndex
                required property int packageIndex

                readonly property bool isRepository: nodeType === "repository"
                readonly property bool isSelected: !isRepository && repoIndex === root.selectedRepoIndex && packageIndex === root.selectedPkgIndex

                implicitWidth: treeView.width
                implicitHeight: isRepository ? 36 : 32
                color: isSelected ? Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.12) : (hoverHandler_.hovered ? (isRepository ? Style.elevated : Qt.rgba(1, 1, 1, 0.02)) : (isRepository ? Style.surface : "transparent"))

                Behavior on color {
                    ColorAnimation {
                        duration: 80
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Style.sm + delegateRoot_.depth * Style.lg
                    anchors.rightMargin: Style.md
                    spacing: Style.xs

                    Text {
                        visible: delegateRoot_.isRepository
                        text: delegateRoot_.expanded ? "▾" : "▸"
                        color: Style.accent
                        font.pixelSize: Style.fontXs
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Rectangle {
                        visible: !delegateRoot_.isRepository
                        implicitWidth: 4
                        implicitHeight: 4
                        radius: 2
                        color: delegateRoot_.isSelected ? Style.accent : Style.textDisabled
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Text {
                        Layout.fillWidth: true
                        text: delegateRoot_.label
                        color: delegateRoot_.isSelected ? Style.accent : (delegateRoot_.isRepository ? Style.textPrimary : Style.textSecondary)
                        font.pixelSize: delegateRoot_.isRepository ? Style.fontSm : Style.fontMd
                        font.bold: delegateRoot_.isRepository
                        font.family: delegateRoot_.isRepository ? font.family : "Consolas, Courier New, monospace"
                        elide: Text.ElideRight
                    }
                }

                HoverHandler {
                    id: hoverHandler_
                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    gesturePolicy: TapHandler.WithinBounds
                    acceptedButtons: Qt.LeftButton
                    onTapped: {
                        if (delegateRoot_.isRepository)
                            root.toggleTopLevelRow(delegateRoot_.treeView, delegateRoot_.row, delegateRoot_.repoIndex);
                        else
                            root.packageSelected(delegateRoot_.repoIndex, delegateRoot_.packageIndex);
                    }
                }

                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: delegateRoot_.isRepository ? 1 : 0
                    color: Style.border
                }
            }

            Text {
                anchors.centerIn: parent
                visible: repositoryTreeView_.rows === 0 && !root.isLoading
                text: qsTr("No repositories available.")
                color: Style.textSecondary
                font.pixelSize: Style.fontMd
            }

            ColumnLayout {
                anchors.centerIn: parent
                spacing: Style.sm
                visible: root.isLoading

                BusyIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    running: root.isLoading
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("Loading repositories...")
                    color: Style.textSecondary
                    font.pixelSize: Style.fontMd
                }
            }
        }
    }
}
