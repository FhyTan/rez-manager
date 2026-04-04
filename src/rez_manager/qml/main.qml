import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "windows"

ApplicationWindow {
    id: root
    title: "rez-manager"
    width:  1300
    height: 820
    minimumWidth:  960
    minimumHeight: 600
    visible: true
    color: s_.bg

    Style { id: s_ }

    // ── Sub-windows (instantiated here, shown on demand) ──────
    SettingsDialog       { id: settingsDlg;  anchors.centerIn: root.contentItem }
    ContextEditorDialog  { id: editorDlg;    anchors.centerIn: root.contentItem }
    PackageManagerWindow { id: pkgManagerWin;  visible: false }
    ContextPreviewWindow { id: previewWin;     visible: false }

    // ── State ─────────────────────────────────────────────────
    property int  selectedProjectIndex: 0
    property string selectedProject: projectsModel.count > 0
        ? projectsModel.get(selectedProjectIndex).name : ""

    // ── Data models ───────────────────────────────────────────
    ListModel {
        id: projectsModel
        ListElement { name: "VFX Pipeline";      avatarColor: "#5F83FF" }
        ListElement { name: "Maya Rigging";       avatarColor: "#4DB880" }
        ListElement { name: "Houdini FX";         avatarColor: "#D98A38" }
        ListElement { name: "USD Pipeline";       avatarColor: "#8A58D8" }
    }

    ListModel {
        id: contextsModel

        // VFX Pipeline
        ListElement {
            project:      "VFX Pipeline"
            name:         "Maya 2024 Base"
            description:  "Base Maya 2024 environment with Arnold renderer and USD support."
            launchTarget: "maya"
            packages:     "maya-2024,python-3.11,mtoa-5.3,usd-23.11,openexr-3.1"
        }
        ListElement {
            project:      "VFX Pipeline"
            name:         "Nuke 14 Comp"
            description:  "Compositing environment with Nuke 14, NukeX and OCIO 2 support."
            launchTarget: "custom"
            packages:     "nuke-14.0,python-3.10,nukex-14.0,ocio-2.2,ffmpeg-6.0"
        }
        ListElement {
            project:      "VFX Pipeline"
            name:         "Shell Dev"
            description:  "Development shell with Python tools and build utilities."
            launchTarget: "shell"
            packages:     "python-3.11,cmake-3.27,git-2.42,ninja-1.11,ruff-0.1"
        }

        // Maya Rigging
        ListElement {
            project:      "Maya Rigging"
            name:         "Rigging Tools"
            description:  "Full rigging environment with mGear, CGM tools and Pyblish."
            launchTarget: "maya"
            packages:     "maya-2024,python-3.11,mgear-4.1,cgm-2.0,pyblish-2.0,pyqt5-5.15"
        }
        ListElement {
            project:      "Maya Rigging"
            name:         "QC Validation"
            description:  "Quality control and validation toolchain."
            launchTarget: "shell"
            packages:     "python-3.11,pytest-7.4,mypy-1.5,ruff-0.1"
        }

        // Houdini FX
        ListElement {
            project:      "Houdini FX"
            name:         "Houdini 20.5"
            description:  "Standard Houdini FX environment with Karma renderer and MaterialX."
            launchTarget: "houdini"
            packages:     "houdini-20.5,python-3.11,karma-1.0,materialx-1.38"
        }
        ListElement {
            project:      "Houdini FX"
            name:         "Houdini + Redshift"
            description:  "Houdini environment with Redshift GPU renderer plugin."
            launchTarget: "houdini"
            packages:     "houdini-20.5,python-3.11,redshift-3.5,redshift-houdini-3.5"
        }

        // USD Pipeline
        ListElement {
            project:      "USD Pipeline"
            name:         "USD Tools"
            description:  "Universal Scene Description toolset for pipeline integration."
            launchTarget: "shell"
            packages:     "python-3.11,usd-23.11,hdstorm-23.11,materialx-1.38,openexr-3.1"
        }
    }

    // ── Helpers ───────────────────────────────────────────────
    function filteredContexts() {
        var result = []
        for (var i = 0; i < contextsModel.count; i++) {
            var c = contextsModel.get(i)
            if (c.project === selectedProject) {
                result.push({
                    project:      c.project,
                    name:         c.name,
                    description:  c.description,
                    launchTarget: c.launchTarget,
                    packages:     c.packages
                })
            }
        }
        return result
    }

    function contextCountFor(projectName) {
        var count = 0
        for (var i = 0; i < contextsModel.count; i++) {
            if (contextsModel.get(i).project === projectName) count++
        }
        return count
    }

    // ── Menu bar ──────────────────────────────────────────────
    menuBar: MenuBar {
        background: Rectangle { color: s_.surface; height: 32 }

        Menu {
            title: "File"
            background: Rectangle { color: s_.elevated; radius: s_.radiusSm; border.width: 1; border.color: s_.borderBright }
            delegate: MenuItem {
                id: menuItem_
                background: Rectangle { color: menuItem_.highlighted ? s_.border : "transparent" }
                contentItem: Text {
                    leftPadding: 16
                    text:  menuItem_.text
                    color: s_.textPrimary
                    font.pixelSize: s_.fontMd
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Action { text: "Settings…"; onTriggered: settingsDlg.open() }
            MenuSeparator {}
            Action { text: "Quit"; onTriggered: Qt.quit() }
        }

        Menu {
            title: "Help"
            background: Rectangle { color: s_.elevated; radius: s_.radiusSm; border.width: 1; border.color: s_.borderBright }
            delegate: MenuItem {
                id: helpItem_
                background: Rectangle { color: helpItem_.highlighted ? s_.border : "transparent" }
                contentItem: Text {
                    leftPadding: 16
                    text:  helpItem_.text
                    color: s_.textPrimary
                    font.pixelSize: s_.fontMd
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Action { text: "About rez-manager" }
        }
    }

    // ── Main layout ───────────────────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ──────────────────────────────────────────────────────
        // SIDEBAR
        // ──────────────────────────────────────────────────────
        Rectangle {
            id: sidebar_
            Layout.fillHeight: true
            width: 240
            color: s_.sidebar

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // App header
                Rectangle {
                    Layout.fillWidth: true
                    height: 56
                    color: "transparent"

                    RowLayout {
                        anchors { fill: parent; leftMargin: s_.lg; rightMargin: s_.lg }
                        spacing: s_.sm

                        Rectangle {
                            width: 30; height: 30; radius: s_.radiusSm
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: s_.accent }
                                GradientStop { position: 1.0; color: "#8A58D8" }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "R"; color: "white"
                                font.pixelSize: s_.fontLg; font.bold: true
                            }
                        }

                        Text {
                            text:           "rez-manager"
                            color:          s_.textPrimary
                            font.pixelSize: s_.fontLg
                            font.bold:      true
                        }
                        Item { Layout.fillWidth: true }
                    }
                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
                }

                // Section label
                Item {
                    Layout.fillWidth: true
                    height: 32
                    Text {
                        anchors { left: parent.left; leftMargin: s_.lg; verticalCenter: parent.verticalCenter }
                        text:           "PROJECTS"
                        color:          s_.textDisabled
                        font.pixelSize: s_.fontXs
                        font.bold:      true
                        font.letterSpacing: 1.5
                    }
                }

                // Project list
                ListView {
                    id: projectList_
                    Layout.fillWidth:  true
                    Layout.fillHeight: true
                    clip: true
                    model: projectsModel
                    spacing: 2

                    ScrollIndicator.vertical: ScrollIndicator {}

                    delegate: Item {
                        width: ListView.view.width
                        height: 44

                        ProjectListItem {
                            anchors { fill: parent; leftMargin: 6; rightMargin: 6 }
                            projectName:  name
                            avatarColor:  model.avatarColor
                            selected:     root.selectedProjectIndex === index
                            contextCount: root.contextCountFor(name)
                            onClicked:    root.selectedProjectIndex = index
                        }
                    }
                }

                // Sidebar bottom toolbar
                Rectangle {
                    Layout.fillWidth: true
                    height: 52
                    color: "transparent"
                    Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: s_.border }

                    RowLayout {
                        anchors { fill: parent; leftMargin: s_.md; rightMargin: s_.md }
                        spacing: s_.xs
                        CardButton { icon: "+"; label: "Project" }
                        Item { Layout.fillWidth: true }
                        CardButton { icon: "⚙"; onClicked: settingsDlg.open() }
                    }
                }
            }
        }

        // Sidebar right border
        Rectangle { width: 1; Layout.fillHeight: true; color: s_.border }

        // ──────────────────────────────────────────────────────
        // CONTENT AREA
        // ──────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            color: s_.bg

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Content header
                Rectangle {
                    Layout.fillWidth: true
                    height: 56
                    color: s_.surface

                    RowLayout {
                        anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.xl }
                        spacing: s_.md

                        ColumnLayout {
                            spacing: 1
                            Text {
                                text:           root.selectedProject.length > 0 ? root.selectedProject : "No project selected"
                                color:          s_.textPrimary
                                font.pixelSize: s_.fontXl
                                font.bold:      true
                            }
                            Text {
                                text:           root.filteredContexts().length + " contexts"
                                color:          s_.textSecondary
                                font.pixelSize: s_.fontSm
                            }
                        }

                        Item { Layout.fillWidth: true }

                        // Context actions
                        CardButton { icon: "+"; label: "New Context"; accent: true; onClicked: editorDlg.open() }
                        CardButton { icon: "⧉"; label: "Duplicate" }
                        CardButton { icon: "✕"; label: "Delete"; danger: true }
                    }
                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
                }

                // Context cards grid
                ScrollView {
                    Layout.fillWidth:  true
                    Layout.fillHeight: true
                    clip: true

                    Flickable {
                        contentWidth:  width
                        contentHeight: cardsFlow_.implicitHeight + s_.xl * 2

                        Flow {
                            id: cardsFlow_
                            x: s_.xl
                            y: s_.xl
                            width:   parent.width - s_.xl * 2
                            spacing: s_.lg

                            Repeater {
                                model: root.filteredContexts()

                                ContextCard {
                                    contextName:  modelData.name
                                    projectName:  modelData.project
                                    description:  modelData.description
                                    launchTarget: modelData.launchTarget
                                    packages:     modelData.packages

                                    onEditInfoRequested: {
                                        editorDlg.contextNameValue = modelData.name
                                        editorDlg.open()
                                    }
                                    onEditPackagesRequested: {
                                        pkgManagerWin.contextName_ = modelData.name
                                        pkgManagerWin.projectName_ = modelData.project
                                        pkgManagerWin.show()
                                    }
                                    onPreviewRequested: {
                                        previewWin.contextName_ = modelData.name
                                        previewWin.projectName_ = modelData.project
                                        previewWin.show()
                                    }
                                    onLaunchRequested: {
                                        launchToast_.projectName = modelData.project
                                        launchToast_.contextName = modelData.name
                                        launchToast_.show()
                                    }
                                }
                            }

                            // Empty state
                            Rectangle {
                                visible: root.filteredContexts().length === 0
                                width:   300
                                height:  160
                                radius:  s_.radiusLg
                                color:   "transparent"
                                border.width: 1
                                border.color: s_.border

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: s_.md
                                    Text { Layout.alignment: Qt.AlignHCenter; text: "⊞"; font.pixelSize: 36; color: s_.textDisabled }
                                    Text { Layout.alignment: Qt.AlignHCenter; text: "No contexts yet"; color: s_.textSecondary; font.pixelSize: s_.fontLg; font.bold: true }
                                    Text { Layout.alignment: Qt.AlignHCenter; text: "Create your first context to get started."; color: s_.textDisabled; font.pixelSize: s_.fontMd }
                                    CardButton {
                                        Layout.alignment: Qt.AlignHCenter
                                        label: "New Context"; accent: true
                                        onClicked: editorDlg.open()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Launch toast notification ──────────────────────────────
    Rectangle {
        id: launchToast_
        property string projectName: ""
        property string contextName: ""

        function show() {
            visible = true
            hideTimer_.restart()
        }

        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: s_.xl }
        width:   toastRow_.implicitWidth + s_.xl
        height:  44
        radius:  s_.radius
        color:   s_.elevated
        border.width: 1
        border.color: s_.borderBright
        visible: false
        opacity: visible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 200 } }

        Timer { id: hideTimer_; interval: 3000; onTriggered: launchToast_.visible = false }

        Row {
            id: toastRow_
            anchors.centerIn: parent
            spacing: s_.sm
            Rectangle { width: 8; height: 8; radius: 4; color: s_.success; anchors.verticalCenter: parent.verticalCenter }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text:           "Launching: " + launchToast_.projectName + " / " + launchToast_.contextName
                color:          s_.textPrimary
                font.pixelSize: s_.fontMd
            }
        }
    }
}
