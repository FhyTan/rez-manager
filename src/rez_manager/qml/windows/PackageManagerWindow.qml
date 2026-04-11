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

    ListModel {
        id: currentPkgsModel
        ListElement { pkgName: "maya"; version: "2024.0" }
        ListElement { pkgName: "python"; version: "3.11.0" }
        ListElement { pkgName: "mtoa"; version: "5.3.4" }
        ListElement { pkgName: "usd"; version: "23.11" }
        ListElement { pkgName: "openexr"; version: "3.1.10" }
    }

    property var repoTree: [
        {
            label: "maya  [/packages/maya]",
            packages: ["maya", "mtoa", "yeti", "bifrost", "mgear", "pyblish"]
        },
        {
            label: "houdini  [/packages/houdini]",
            packages: ["houdini", "karma", "redshift", "redshift-houdini", "vellum-tools"]
        },
        {
            label: "base  [/packages/base]",
            packages: ["python", "cmake", "git", "openexr", "usd", "materialx", "boost", "tbb"]
        }
    ]

    property int selectedRepoIndex: 0
    property int selectedPkgIndex: -1
    property string selectedPkgName: {
        if (selectedPkgIndex < 0 || selectedRepoIndex < 0)
            return ""

        const repo = repoTree[selectedRepoIndex]
        if (!repo || selectedPkgIndex >= repo.packages.length)
            return ""

        return repo.packages[selectedPkgIndex]
    }

    readonly property var pkgDetail: ({
        name: selectedPkgName.length > 0 ? selectedPkgName : "—",
        versions: ["2024.0", "2023.3", "2023.0", "2022.5"],
        description: selectedPkgName === "maya"
            ? "Autodesk Maya 3D animation and visual effects software."
            : selectedPkgName.length > 0
                ? "A package providing " + selectedPkgName + " tools and libraries."
                : "Select a package to see details.",
        requires: ["python-3.11", "openexr-3.1", "tbb-2021"],
        variants: ["platform-linux arch-x86_64", "platform-windows arch-x86_64"],
        tools: selectedPkgName === "maya"
            ? ["maya", "mayapy", "mayabatch"]
            : ["python3", "pip3"],
        code: "name = '" + (selectedPkgName.length > 0 ? selectedPkgName : "package")
            + "'\nversion = '2024.0'\nrequires = ['python-3.11+']\n\n"
            + "def commands():\n    env.PATH.prepend('{root}/bin')\n"
            + "    env.MAYA_LOCATION = '{root}'\n"
    })

    property int selectedDetailVersion: 0

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
                        text: currentPkgsModel.count + " packages"
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
                packagesModel: currentPkgsModel
                onRemoveRequested: function(index) {
                    currentPkgsModel.remove(index)
                }
            }

            PackageRepositoryPanel {
                SplitView.preferredWidth: 260
                SplitView.minimumWidth: 180
                repoTree: root.repoTree
                selectedRepoIndex: root.selectedRepoIndex
                selectedPkgIndex: root.selectedPkgIndex
                onRepositoryToggled: function(index) {
                    root.selectedRepoIndex = root.selectedRepoIndex === index ? -1 : index
                    root.selectedPkgIndex = -1
                    root.selectedDetailVersion = 0
                }
                onPackageSelected: function(repoIndex, pkgIndex) {
                    root.selectedRepoIndex = repoIndex
                    root.selectedPkgIndex = pkgIndex
                    root.selectedDetailVersion = 0
                }
            }

            PackageDetailPanel {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 320
                selectedPkgName: root.selectedPkgName
                pkgDetail: root.pkgDetail
                selectedDetailVersion: root.selectedDetailVersion
                onDetailVersionSelected: function(index) {
                    root.selectedDetailVersion = index
                }
                onAddPackageRequested: function(pkgName, version) {
                    if (pkgName.length === 0)
                        return

                    currentPkgsModel.append({
                        pkgName: pkgName,
                        version: version
                    })
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
                CardButton { label: "Save"; accent: true }
            }
        }
    }
}
