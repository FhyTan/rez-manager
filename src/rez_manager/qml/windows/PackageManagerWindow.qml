import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."
import "../components"

// Package manager window — edit the dependencies of a context.
// Three-panel layout: current packages | repository browser | package detail
Window {
    id: root
    title: "Packages — " + projectName_ + "  /  " + contextName_
    width:  1100
    height: 720
    color:  s_.bg
    flags:  Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    property string contextName_: "Maya 2024 Base"
    property string projectName_: "VFX Pipeline"

    Style { id: s_ }

    // ── Dummy data ────────────────────────────────────────────
    ListModel {
        id: currentPkgsModel
        ListElement { pkgName: "maya";    version: "2024.0" }
        ListElement { pkgName: "python";  version: "3.11.0" }
        ListElement { pkgName: "mtoa";    version: "5.3.4"  }
        ListElement { pkgName: "usd";     version: "23.11"  }
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
        if (selectedPkgIndex < 0 || selectedRepoIndex < 0) return ""
        var repo = repoTree[selectedRepoIndex]
        if (!repo || selectedPkgIndex >= repo.packages.length) return ""
        return repo.packages[selectedPkgIndex]
    }

    // Detail for the selected package (dummy values)
    readonly property var pkgDetail: ({
        name:         selectedPkgName.length > 0 ? selectedPkgName : "—",
        versions:     ["2024.0", "2023.3", "2023.0", "2022.5"],
        description:  selectedPkgName === "maya"
            ? "Autodesk Maya 3D animation and visual effects software."
            : selectedPkgName.length > 0
            ? "A package providing " + selectedPkgName + " tools and libraries."
            : "Select a package to see details.",
        requires:     ["python-3.11", "openexr-3.1", "tbb-2021"],
        variants:     ["platform-linux arch-x86_64", "platform-windows arch-x86_64"],
        tools:        selectedPkgName === "maya"
            ? ["maya", "mayapy", "mayabatch"]
            : ["python3", "pip3"],
        code:         "name = '" + (selectedPkgName.length > 0 ? selectedPkgName : "package") + "'\nversion = '2024.0'\nrequires = ['python-3.11+']\n\ndef commands():\n    env.PATH.prepend('{root}/bin')\n    env.MAYA_LOCATION = '{root}'\n"
    })

    property int selectedDetailVersion: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Header ────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 56; color: s_.surface
            RowLayout {
                anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.xl }
                ColumnLayout {
                    spacing: 2
                    Text { text: root.projectName_; color: s_.textSecondary; font.pixelSize: s_.fontSm }
                    Text { text: root.contextName_; color: s_.textPrimary; font.pixelSize: s_.fontLg; font.bold: true }
                }
                Item { Layout.fillWidth: true }
                Badge { text: currentPkgsModel.count + " packages"; badgeColor: s_.accent }
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
        }

        // ── Three-panel split ─────────────────────────────────
        SplitView {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            orientation: Qt.Horizontal
            handle: Rectangle {
                implicitWidth: 1; color: s_.border
                Rectangle {
                    anchors.centerIn: parent
                    width: 1; height: parent.height
                    color: SplitHandle.hovered || SplitHandle.pressed ? s_.accent : s_.border
                    Behavior on color { ColorAnimation { duration: 100 } }
                }
            }

            // ── Left: current packages ─────────────────────────
            Rectangle {
                SplitView.preferredWidth: 240
                SplitView.minimumWidth:   160
                color: s_.surface

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    // Panel header
                    Rectangle {
                        Layout.fillWidth: true; height: 40; color: "transparent"
                        RowLayout {
                            anchors { fill: parent; leftMargin: s_.md; rightMargin: s_.sm }
                            Text { text: "Current Packages"; color: s_.textSecondary; font.pixelSize: s_.fontSm; font.bold: true; Layout.fillWidth: true }
                            CardButton { icon: "+"; onClicked: {} }
                        }
                        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
                    }

                    ListView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        model: currentPkgsModel
                        clip: true
                        ScrollIndicator.vertical: ScrollIndicator {}

                        delegate: Rectangle {
                            width: ListView.view.width; height: 42
                            color: delHov_.containsMouse ? s_.elevated : "transparent"
                            Behavior on color { ColorAnimation { duration: 80 } }

                            RowLayout {
                                anchors { fill: parent; leftMargin: s_.md; rightMargin: s_.sm }
                                spacing: s_.sm
                                Rectangle { width: 6; height: 6; radius: 3; color: s_.accent; Layout.alignment: Qt.AlignVCenter }
                                ColumnLayout {
                                    Layout.fillWidth: true; spacing: 1
                                    Text { text: pkgName; color: s_.textPrimary; font.pixelSize: s_.fontMd; font.bold: true }
                                    Text { text: version; color: s_.textSecondary; font.pixelSize: s_.fontXs; font.family: "Consolas, Courier New, monospace" }
                                }
                                CardButton { icon: "✕"; danger: true }
                            }
                            MouseArea { id: delHov_; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                        }
                    }
                }
            }

            // ── Center: repository browser ─────────────────────
            Rectangle {
                SplitView.preferredWidth: 260
                SplitView.minimumWidth:   180
                color: s_.bg

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true; height: 40; color: "transparent"
                        Text { anchors.left: parent.left; anchors.leftMargin: s_.md; anchors.verticalCenter: parent.verticalCenter; text: "Repository Browser"; color: s_.textSecondary; font.pixelSize: s_.fontSm; font.bold: true }
                        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
                    }

                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.parent.width
                            spacing: 0

                            Repeater {
                                model: root.repoTree

                                ColumnLayout {
                                    required property var modelData
                                    required property int index
                                    Layout.fillWidth: true
                                    spacing: 0

                                    // Repository header
                                    Rectangle {
                                        Layout.fillWidth: true; height: 36
                                        color: repoHov_.containsMouse ? s_.elevated : s_.surface
                                        Behavior on color { ColorAnimation { duration: 80 } }

                                        RowLayout {
                                            anchors { fill: parent; leftMargin: s_.sm; rightMargin: s_.sm }
                                            spacing: s_.xs
                                            Text {
                                                text: root.selectedRepoIndex === index ? "▾" : "▸"
                                                color: s_.accent; font.pixelSize: s_.fontXs
                                                Layout.alignment: Qt.AlignVCenter
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text:            modelData.label
                                                color:           s_.textPrimary
                                                font.pixelSize:  s_.fontSm
                                                font.bold:       true
                                                elide:           Text.ElideRight
                                            }
                                        }
                                        MouseArea {
                                            id: repoHov_; anchors.fill: parent; hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                root.selectedRepoIndex = root.selectedRepoIndex === index ? -1 : index
                                                root.selectedPkgIndex = -1
                                            }
                                        }
                                        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
                                    }

                                    // Package items (shown when repo is expanded)
                                    Repeater {
                                        model: root.selectedRepoIndex === index ? modelData.packages : []
                                        Rectangle {
                                            required property string modelData   // package name
                                            required property int    index       // pkgIndex
                                            Layout.fillWidth: true; height: 32
                                            // parent here is the outer ColumnLayout (repoContainer)
                                            // parent.index == repoIndex; own index == pkgIndex
                                            property bool isSelected: root.selectedRepoIndex === parent.index
                                                                   && root.selectedPkgIndex  === index
                                            color: isSelected
                                                ? Qt.rgba(s_.accent.r, s_.accent.g, s_.accent.b, 0.12)
                                                : (pkgHov_.containsMouse ? s_.elevated : "transparent")
                                            Behavior on color { ColorAnimation { duration: 80 } }

                                            RowLayout {
                                                anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.md }
                                                Rectangle { width: 4; height: 4; radius: 2; color: isSelected ? s_.accent : s_.textDisabled; Layout.alignment: Qt.AlignVCenter }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text:            modelData
                                                    color:           isSelected ? s_.accent : s_.textSecondary
                                                    font.pixelSize:  s_.fontMd
                                                    font.family:     "Consolas, Courier New, monospace"
                                                    elide:           Text.ElideRight
                                                }
                                            }
                                            MouseArea {
                                                id: pkgHov_; anchors.fill: parent; hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    // parent = this Rectangle; parent.parent = outer ColumnLayout
                                                    root.selectedRepoIndex = parent.parent.index
                                                    root.selectedPkgIndex  = parent.index
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Right: package detail ──────────────────────────
            Rectangle {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 280
                color: s_.surface

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true; height: 40; color: "transparent"
                        Text { anchors.left: parent.left; anchors.leftMargin: s_.md; anchors.verticalCenter: parent.verticalCenter; text: "Package Detail"; color: s_.textSecondary; font.pixelSize: s_.fontSm; font.bold: true }
                        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
                    }

                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        clip: true
                        visible: root.selectedPkgName.length > 0

                        ColumnLayout {
                            width: parent.parent.width - s_.xl
                            x: s_.lg; y: s_.lg
                            spacing: s_.lg

                            // Name + version
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: root.pkgDetail.name; color: s_.textPrimary; font.pixelSize: s_.fontXl; font.bold: true; Layout.fillWidth: true }
                                ComboBox {
                                    id: versionCombo_
                                    model: root.pkgDetail.versions
                                    width: 120
                                    currentIndex: root.selectedDetailVersion
                                    onCurrentIndexChanged: root.selectedDetailVersion = currentIndex
                                    background: Rectangle { color: s_.elevated; radius: s_.radiusSm; border.width: 1; border.color: s_.border }
                                    contentItem: Text { leftPadding: s_.sm; text: parent.displayText; color: s_.textPrimary; font.pixelSize: s_.fontMd; verticalAlignment: Text.AlignVCenter }
                                    delegate: ItemDelegate {
                                        width: parent ? parent.width : 0; height: 32
                                        background: Rectangle { color: parent.hovered ? s_.elevated : "transparent" }
                                        contentItem: Text { leftPadding: s_.sm; text: modelData; color: s_.textPrimary; font.pixelSize: s_.fontMd; verticalAlignment: Text.AlignVCenter }
                                    }
                                    popup: Popup {
                                        y: parent.height + 2; width: parent.width
                                        background: Rectangle { color: s_.card; radius: s_.radiusSm; border.width: 1; border.color: s_.borderBright }
                                        contentItem: ListView { implicitHeight: Math.min(contentHeight, 200); model: parent.parent.delegateModel; clip: true }
                                    }
                                }
                            }

                            // Add to packages button
                            CardButton {
                                label: "Add  " + root.pkgDetail.name + "  " + (root.pkgDetail.versions[root.selectedDetailVersion] || "")
                                accent: true
                                Layout.fillWidth: true
                                implicitHeight: 38
                                onClicked: currentPkgsModel.append({ pkgName: root.pkgDetail.name, version: root.pkgDetail.versions[root.selectedDetailVersion] || "" })
                            }

                            // Description
                            DetailSection { title: "Description"; body: root.pkgDetail.description }

                            // Requires
                            DetailSection {
                                title: "Requires"
                                body: root.pkgDetail.requires.join("\n")
                                monospace: true
                            }

                            // Tools
                            DetailSection {
                                title: "Tools"
                                body: root.pkgDetail.tools.join("\n")
                                monospace: true
                            }

                            // Variants
                            DetailSection {
                                title: "Variants"
                                body: root.pkgDetail.variants.join("\n")
                                monospace: true
                            }

                            // Python snippet
                            DetailSection {
                                title: "package.py"
                                body: root.pkgDetail.code
                                monospace: true
                                codeStyle: true
                            }
                        }
                    }

                    // Empty state
                    Item {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        visible: root.selectedPkgName.length === 0
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: s_.md
                            Text { Layout.alignment: Qt.AlignHCenter; text: "⊟"; font.pixelSize: 40; color: s_.textDisabled }
                            Text { Layout.alignment: Qt.AlignHCenter; text: "Select a package to see details"; color: s_.textDisabled; font.pixelSize: s_.fontMd }
                        }
                    }
                }
            }
        }

        // ── Footer ────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; height: 52
            color: s_.surface
            Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: s_.border }
            RowLayout {
                anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.xl }
                CardButton { icon: "◉"; label: "Preview Resolve" }
                Item { width: s_.sm }
                CardButton { icon: "⌘"; label: "Launch Console" }
                Item { Layout.fillWidth: true }
                CardButton { label: "Cancel"; onClicked: root.close() }
                Item { width: s_.sm }
                CardButton { label: "Save"; accent: true }
            }
        }
    }

    // Inline helper component for detail sections
    component DetailSection: ColumnLayout {
        property string title:     ""
        property string body:      ""
        property bool   monospace: false
        property bool   codeStyle: false
        Style { id: s_ }
        spacing: s_.xs
        Layout.fillWidth: true

        Text {
            text:           title
            color:          s_.textSecondary
            font.pixelSize: s_.fontXs
            font.bold:      true
            font.letterSpacing: 0.5
        }
        Rectangle {
            Layout.fillWidth: true
            height:       bodyText_.implicitHeight + (codeStyle ? s_.md * 2 : 0)
            radius:       codeStyle ? s_.radiusSm : 0
            color:        codeStyle ? s_.elevated : "transparent"
            border.width: codeStyle ? 1 : 0
            border.color: s_.border
            Text {
                id: bodyText_
                anchors {
                    fill: parent
                    leftMargin:  codeStyle ? s_.md : 0
                    rightMargin: codeStyle ? s_.md : 0
                    topMargin:   codeStyle ? s_.sm : 0
                    bottomMargin: codeStyle ? s_.sm : 0
                }
                text:           body.length > 0 ? body : "—"
                color:          body.length > 0 ? s_.textPrimary : s_.textDisabled
                font.pixelSize: s_.fontSm
                font.family:    monospace ? "Consolas, Courier New, monospace" : font.family
                wrapMode:       Text.WordWrap
            }
        }
    }
}
