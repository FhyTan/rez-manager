pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

// Package manager window — edit the dependencies of a context.
// Three-panel layout: required packages | repository browser | package detail
Window {
    id: root
    title: "Packages — " + projectName_ + "  /  " + contextName_
    width: 1100
    height: 720
    color: Style.bg
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

    property string contextName_: "Maya 2024 Base"
    property string projectName_: "VFX Pipeline"
    property var packageManagerController: null

    property int selectedRepoIndex: -1
    property int selectedPkgIndex: -1
    signal saved(string projectName, string contextName)

    function loadContext(projectName, contextName) {
        selectedRepoIndex = -1;
        selectedPkgIndex = -1;
        if (!packageManagerController)
            return false;
        if (!packageManagerController.loadContext(projectName, contextName))
            return false;
        projectName_ = projectName;
        contextName_ = contextName;
        return true;
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 56
            color: Style.surface

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.xl
                anchors.rightMargin: Style.xl
                spacing: 2

                Item { Layout.fillHeight: true }

                RowLayout {
                    Text {
                        text: root.projectName_ + "  /  " + root.contextName_
                        color: Style.textPrimary
                        font.pixelSize: Style.fontLg
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    Badge {
                        text: root.packageManagerController
                            ? root.packageManagerController.packageCount + " packages"
                            : "0 packages"
                        badgeColor: Style.accent
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            handle: Rectangle {
                implicitWidth: 1
                color: Style.border

                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: parent.height
                    color: SplitHandle.hovered || SplitHandle.pressed ? Style.accent : Style.border

                    Behavior on color {
                        ColorAnimation { duration: 100 }
                    }
                }
            }

            RequiredPackagesPanel {
                SplitView.preferredWidth: 240
                SplitView.minimumWidth: 160
                packagesModel: root.packageManagerController
                    ? root.packageManagerController.packageRequestsModel
                    : null
                onRemoveRequested: function(index) {
                    if (root.packageManagerController)
                        root.packageManagerController.removePackageRequest(index);
                }
            }

            PackageRepositoryPanel {
                SplitView.preferredWidth: 260
                SplitView.minimumWidth: 180
                repoTree: root.packageManagerController ? root.packageManagerController.repositoryTree : []
                selectedRepoIndex: root.selectedRepoIndex
                selectedPkgIndex: root.selectedPkgIndex
                onRepositoryToggled: function(index) {
                    root.selectedRepoIndex = root.selectedRepoIndex === index ? -1 : index;
                    root.selectedPkgIndex = -1;
                    if (root.packageManagerController)
                        root.packageManagerController.clearSelection();
                }
                onPackageSelected: function(repoIndex, pkgIndex) {
                    root.selectedRepoIndex = repoIndex;
                    root.selectedPkgIndex = pkgIndex;
                    if (root.packageManagerController)
                        root.packageManagerController.selectPackage(repoIndex, pkgIndex);
                }
            }

            PackageDetailPanel {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 320
                selectedPkgName: root.packageManagerController
                    ? root.packageManagerController.packageDetail.name || ""
                    : ""
                pkgDetail: root.packageManagerController
                    ? root.packageManagerController.packageDetail
                    : ({})
                selectedDetailVersion: root.packageManagerController
                    ? root.packageManagerController.selectedDetailVersion
                    : -1
                onDetailVersionSelected: function(index) {
                    if (root.packageManagerController)
                        root.packageManagerController.selectDetailVersion(index);
                }
                onAddPackageRequested: function(pkgName, version) {
                    if (root.packageManagerController)
                        root.packageManagerController.addPackageRequest(pkgName, version);
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 52
            color: Style.surface

            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: Style.border
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.xl
                anchors.rightMargin: Style.xl

                CardButton { glyph: "◉"; label: "Preview Resolve" }
                Item { width: Style.sm }
                CardButton { glyph: "⌘"; label: "Launch Console" }
                Item { Layout.fillWidth: true }
                CardButton { label: "Cancel"; onClicked: root.close() }
                Item { width: Style.sm }
                CardButton {
                    label: "Save"
                    accent: true
                    onClicked: {
                        if (!root.packageManagerController || !root.packageManagerController.save())
                            return;

                        root.saved(root.projectName_, root.contextName_);
                        root.close();
                    }
                }
            }
        }
    }
}
