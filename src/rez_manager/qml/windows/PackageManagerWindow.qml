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

    property string contextName_: ""
    property string projectName_: ""
    property var packageManagerController: null
    property var contextPreviewController: null
    property var contextLauncherController: null

    signal saved(string projectName, string contextName)
    signal previewRequested
    signal launchConsoleRequested(string projectName, string contextName)

    function loadContext(projectName, contextName) {
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
            implicitHeight: 56
            color: Style.surface

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.xl
                anchors.rightMargin: Style.xl
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
                        text: root.packageManagerController ? root.packageManagerController.packageCount + " packages" : "0 packages"
                        badgeColor: Style.accent
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
                        ColorAnimation {
                            duration: 100
                        }
                    }
                }
            }

            RequiredPackagesPanel {
                SplitView.preferredWidth: 240
                SplitView.minimumWidth: 160
                packagesModel: root.packageManagerController ? root.packageManagerController.packageRequestsModel : null
                selectedRow: root.packageManagerController ? root.packageManagerController.selectedRequestRow : -1
                onPackageSelected: function (index) {
                    if (root.packageManagerController)
                        root.packageManagerController.selectRequiredPackage(index);
                }
                onRemoveRequested: function (index) {
                    if (root.packageManagerController)
                        root.packageManagerController.removePackageRequest(index);
                }
            }

            PackageRepositoryPanel {
                SplitView.preferredWidth: 260
                SplitView.minimumWidth: 180
                repositoryModel: root.packageManagerController ? root.packageManagerController.repositoryModel : null
                selectedRepoIndex: root.packageManagerController ? root.packageManagerController.selectedRepositoryIndex : -1
                selectedPkgIndex: root.packageManagerController ? root.packageManagerController.selectedRepositoryPackageIndex : -1
                onPackageSelected: function (repoIndex, pkgIndex) {
                    if (root.packageManagerController)
                        root.packageManagerController.selectRepositoryPackage(repoIndex, pkgIndex);
                }
            }

            PackageDetailPanel {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 320
                packageDetail: root.packageManagerController ? root.packageManagerController.packageDetail : null
                onDetailVersionSelected: function (index) {
                    if (root.packageManagerController)
                        root.packageManagerController.selectDetailVersion(index);
                }
                onAddPackageRequested: function (pkgName, version) {
                    if (root.packageManagerController)
                        root.packageManagerController.addPackageRequest(pkgName, version);
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 52
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

                CardButton {
                    glyph: "◉"
                    label: "Preview Resolve"
                    onClicked: {
                        if (!root.packageManagerController || !root.contextPreviewController)
                            return;
                        if (!root.contextPreviewController.loadPackageRequests(root.projectName_, root.contextName_, root.packageManagerController.packageRequests))
                            return;
                        root.previewRequested();
                    }
                }
                Item {
                    Layout.preferredWidth: Style.sm
                }
                CardButton {
                    glyph: "⌘"
                    label: "Launch Console"
                    onClicked: {
                        if (!root.packageManagerController || !root.contextLauncherController)
                            return;
                        if (!root.contextLauncherController.launchPackageRequests(root.projectName_, root.contextName_, root.packageManagerController.packageRequests))
                            return;
                        root.launchConsoleRequested(root.projectName_, root.contextName_);
                    }
                }
                Item {
                    Layout.fillWidth: true
                }
                CardButton {
                    label: "Cancel"
                    onClicked: root.close()
                }
                Item {
                    Layout.preferredWidth: Style.sm
                }
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
