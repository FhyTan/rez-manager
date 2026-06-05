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
            selectionBehavior: TableView.SelectRows
            selectionMode: TableView.SingleSelection
            selectionModel: ItemSelectionModel {}

            columnWidthProvider: function (column) {
                return width;
            }

            delegate: TreeViewDelegate {
                id: delegateRoot_
                required property string label
                required property string nodeType
                required property int repoIndex
                required property int packageIndex

                readonly property bool isRepository: nodeType === "repository"

                contentItem: Item {
                    RowLayout {
                        anchors {
                            fill: parent
                            rightMargin: Style.md
                        }
                        spacing: Style.xs

                        Rectangle {
                            visible: !delegateRoot_.isRepository
                            implicitWidth: 4
                            implicitHeight: 4
                            radius: 2
                            color: delegateRoot_.highlighted ? Style.accent : Style.textDisabled
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            Layout.fillWidth: true
                            text: delegateRoot_.label
                            color: delegateRoot_.highlighted ? Style.accent : (delegateRoot_.isRepository ? Style.textPrimary : Style.textSecondary)
                            font.pixelSize: delegateRoot_.isRepository ? Style.fontSm : Style.fontMd
                            font.bold: delegateRoot_.isRepository
                            elide: Text.ElideRight
                        }
                    }

                    TapHandler {
                        gesturePolicy: TapHandler.WithinBounds
                        acceptedButtons: Qt.LeftButton
                        onTapped: {
                            if (delegateRoot_.isRepository)
                                // root.toggleTopLevelRow(delegateRoot_.treeView, delegateRoot_.row, delegateRoot_.repoIndex);
                                repositoryTreeView_.toggleExpanded(delegateRoot_.row);
                            else {
                                root.packageSelected(delegateRoot_.repoIndex, delegateRoot_.packageIndex);
                                repositoryTreeView_.selectionModel.setCurrentIndex(repositoryTreeView_.index(delegateRoot_.row, 0), "SelectCurrent");
                            }
                        }
                    }
                }
            }
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
