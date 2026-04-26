pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager
import ".."
import "../Components"

// Package manager window — edit the dependencies of a context.
// Three-panel layout: required packages | repository browser | package detail
Window {
    id: root
    title: "Packages — " + projectName_ + "  /  " + contextName_
    width: 1100
    height: 720
    color: Style.bg
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
    readonly property string errorTarget_: "package-manager"
    AppErrorTarget.errorTarget: root.errorTarget_

    property string contextName_: ""
    property string projectName_: ""
    readonly property bool repositoriesLoading: packageManagerController_.isLoadingRepositories
    readonly property bool previewLoading: contextPreviewController_.isLoading

    signal saved(string projectName, string contextName)
    signal openLogsRequested

    PackageManagerController {
        id: packageManagerController_
    }
    ContextPreviewController {
        id: contextPreviewController_
    }
    ContextLauncherController {
        id: contextLauncherController_
    }
    ContextPreviewWindow {
        id: previewWin_
        visible: false
        contextPreviewController: contextPreviewController_
    }

    function loadContext(projectName, contextName) {
        if (!packageManagerController_.loadContext(projectName, contextName))
            return false;
        projectName_ = projectName;
        contextName_ = contextName;
        return true;
    }

    function showStatus(message, isError) {
        statusToast_.show(message, isError ? Style.error : Style.success);
    }

    Connections {
        target: AppErrorHub // qmllint disable unqualified
        function onErrorOccurred(message, target) {
            if (target === root.errorTarget_ && root.visible)
                statusToast_.show(message, Style.error);
        }
    }
    Connections {
        target: contextPreviewController_
        function onPreviewResolved() {
            previewWin_.show();
            previewWin_.requestActivate();
        }
    }
    Connections {
        target: contextLauncherController_
        function onLaunchSucceeded(projectName, contextName) {
            root.showStatus("Launching console: " + projectName + " / " + contextName, false);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: header_
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
                    spacing: Style.sm

                    Text {
                        text: root.projectName_ + "  /  " + root.contextName_
                        color: Style.textPrimary
                        font.pixelSize: Style.fontLg
                        font.bold: true
                    }

                    Badge {
                        text: packageManagerController_.packageCount + " packages"
                        badgeColor: Style.accent
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    CardButton {
                        glyph: "↻"
                        label: root.repositoriesLoading ? "Refreshing" : "Refresh"
                        enabled: !root.repositoriesLoading
                        onClicked: packageManagerController_.refresh()
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
            id: content_
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
                packagesModel: packageManagerController_.packageRequestsModel
                selectedRow: packageManagerController_.selectedRequestRow
                onPackageSelected: function (index) {
                    packageManagerController_.selectRequiredPackage(index);
                }
                onRemoveRequested: function (index) {
                    packageManagerController_.removePackageRequest(index);
                }
            }

            PackageRepositoryPanel {
                SplitView.preferredWidth: 260
                SplitView.minimumWidth: 180
                repositoryModel: packageManagerController_.repositoryModel
                selectedRepoIndex: packageManagerController_.selectedRepositoryIndex
                selectedPkgIndex: packageManagerController_.selectedRepositoryPackageIndex
                isLoading: root.repositoriesLoading
                onPackageSelected: function (repoIndex, pkgIndex) {
                    packageManagerController_.selectRepositoryPackage(repoIndex, pkgIndex);
                }
            }

            PackageDetailPanel {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 320
                packageDetail: packageManagerController_.packageDetail
                onDetailVersionSelected: function (index) {
                    packageManagerController_.selectDetailVersion(index);
                }
                onAddPackageRequested: function (pkgName, version) {
                    packageManagerController_.addPackageRequest(pkgName, version);
                }
            }
        }

        Rectangle {
            id: footer_
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
                    label: root.previewLoading ? qsTr("Resolving...") : qsTr("Preview Resolve")
                    enabled: !root.previewLoading
                    onClicked: {
                        if (!contextPreviewController_.loadPackageRequests(root.projectName_, root.contextName_, packageManagerController_.packageRequests))
                            return;
                        statusToast_.show(qsTr("Resolving preview..."), Style.accent);
                    }
                }
                Item {
                    Layout.preferredWidth: Style.sm
                }
                CardButton {
                    glyph: "⌘"
                    label: "Launch Console"
                    onClicked: contextLauncherController_.launchPackageRequests(root.projectName_, root.contextName_, packageManagerController_.packageRequests)
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
                        if (!packageManagerController_.save())
                            return;

                        root.saved(root.projectName_, root.contextName_);
                        root.close();
                    }
                }
            }
        }
    }

    StatusToast {
        id: statusToast_
        onActivated: root.openLogsRequested()
    }
}
