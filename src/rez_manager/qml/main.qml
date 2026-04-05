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

    Style    { id: s_ }
    AppStore { id: store }

    // ── Sub-windows (instantiated here, shown on demand) ──────
    SettingsDialog       { id: settingsDlg;  anchors.centerIn: root.contentItem }
    ContextEditorDialog  { id: editorDlg;    anchors.centerIn: root.contentItem }
    PackageManagerWindow { id: pkgManagerWin;  visible: false }
    ContextPreviewWindow { id: previewWin;     visible: false }

    // ── State ─────────────────────────────────────────────────
    property int    selectedProjectIndex: 0
    property string selectedProject: store.projects.count > 0
        ? store.projects.get(selectedProjectIndex).name : ""

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
                    model: store.projects
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
                            contextCount: store.contextCountFor(name)
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
                                text:           store.filteredContexts(root.selectedProject).length + " contexts"
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
                                model: store.filteredContexts(root.selectedProject)

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
                                visible: store.filteredContexts(root.selectedProject).length === 0
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
