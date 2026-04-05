import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "windows"
import "dummydata"

ApplicationWindow {
    id: root
    title: "rez-manager"
    width: 1080
    height: 760
    minimumWidth: 960
    minimumHeight: 600
    visible: true
    color: Style.bg

    // ── Data models (dummy — swap imports for Python-backed types) ────────────
    ProjectListModel {
        id: projectModel
    }
    RezContextListModel {
        id: contextModel
    }

    // ── Sub-windows (instantiated here, shown on demand) ──────
    SettingsDialog {
        id: settingsDlg
        anchors.centerIn: root.contentItem
    }
    ContextEditorDialog {
        id: editorDlg
        anchors.centerIn: root.contentItem
    }
    PackageManagerWindow {
        id: pkgManagerWin
        visible: false
    }
    ContextPreviewWindow {
        id: previewWin
        visible: false
    }

    // ── State ─────────────────────────────────────────────────
    property int selectedProjectIndex: 0
    property string selectedProject: projectModel.count > 0 ? projectModel.get(selectedProjectIndex).name : ""

    // ── Menu bar ──────────────────────────────────────────────
    menuBar: MenuBar {
        background: Rectangle {
            color: Style.surface
            height: 32
        }

        // Style the menu bar tab labels ("File", "Help", ...)
        delegate: MenuBarItem {
            id: mbi_
            implicitHeight: 32
            background: Rectangle {
                color: mbi_.highlighted ? Style.elevated : "transparent"
                radius: Style.radiusSm
            }
            contentItem: Text {
                text: mbi_.text
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                leftPadding: Style.sm
                rightPadding: Style.sm
            }
        }

        Menu {
            title: "File"
            background: Rectangle {
                color: Style.elevated
                radius: Style.radiusSm
                border.width: 1
                border.color: Style.borderBright
            }
            delegate: MenuItem {
                id: menuItem_
                background: Rectangle {
                    color: menuItem_.highlighted ? Style.border : "transparent"
                }
                contentItem: Text {
                    leftPadding: 16
                    text: menuItem_.text
                    color: Style.textPrimary
                    font.pixelSize: Style.fontMd
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Action {
                text: "Settings…"
                onTriggered: settingsDlg.open()
            }
            MenuSeparator {}
            Action {
                text: "Quit"
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: "Help"
            background: Rectangle {
                color: Style.elevated
                radius: Style.radiusSm
                border.width: 1
                border.color: Style.borderBright
            }
            delegate: MenuItem {
                id: helpItem_
                background: Rectangle {
                    color: helpItem_.highlighted ? Style.border : "transparent"
                }
                contentItem: Text {
                    leftPadding: 16
                    text: helpItem_.text
                    color: Style.textPrimary
                    font.pixelSize: Style.fontMd
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Action {
                text: "About rez-manager"
            }
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
            color: Style.sidebar

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // App header
                Rectangle {
                    Layout.fillWidth: true
                    height: 56
                    color: "transparent"

                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: Style.lg
                            rightMargin: Style.lg
                        }
                        spacing: Style.sm

                        Rectangle {
                            width: 30
                            height: 30
                            radius: Style.radiusSm
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop {
                                    position: 0.0
                                    color: Style.accent
                                }
                                GradientStop {
                                    position: 1.0
                                    color: Style.accentSecondary
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "R"
                                color: Style.white
                                font.pixelSize: Style.fontLg
                                font.bold: true
                            }
                        }

                        Text {
                            text: "rez-manager"
                            color: Style.textPrimary
                            font.pixelSize: Style.fontLg
                            font.bold: true
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                    }
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 1
                        color: Style.border
                    }
                }

                // Section label
                Item {
                    Layout.fillWidth: true
                    height: 32
                    Text {
                        anchors {
                            left: parent.left
                            leftMargin: Style.lg
                            verticalCenter: parent.verticalCenter
                        }
                        text: "PROJECTS"
                        color: Style.textDisabled
                        font.pixelSize: Style.fontXs
                        font.bold: true
                        font.letterSpacing: 1.5
                    }
                }

                // Project list
                ListView {
                    id: projectList_
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: projectModel
                    spacing: 2

                    ScrollIndicator.vertical: ScrollIndicator {}

                    delegate: Item {
                        width: ListView.view.width
                        height: 44

                        ProjectListItem {
                            anchors {
                                fill: parent
                                leftMargin: 6
                                rightMargin: 6
                            }
                            projectName: name
                            avatarColor: model.avatarColor
                            selected: root.selectedProjectIndex === index
                            contextCount: contextModel.contextCountFor(name)
                            onClicked: root.selectedProjectIndex = index
                        }
                    }
                }

                // Sidebar bottom toolbar
                Rectangle {
                    Layout.fillWidth: true
                    height: 52
                    color: "transparent"
                    Rectangle {
                        anchors.top: parent.top
                        width: parent.width
                        height: 1
                        color: Style.border
                    }

                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: Style.md
                            rightMargin: Style.md
                        }
                        spacing: Style.xs
                        CardButton {
                            icon: "+"
                            label: "Project"
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        CardButton {
                            icon: "⚙"
                            onClicked: settingsDlg.open()
                        }
                    }
                }
            }
        }

        // Sidebar right border
        Rectangle {
            width: 1
            Layout.fillHeight: true
            color: Style.border
        }

        // ──────────────────────────────────────────────────────
        // CONTENT AREA
        // ──────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Style.bg

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Content header
                Rectangle {
                    Layout.fillWidth: true
                    height: 56
                    color: Style.surface

                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: Style.xl
                            rightMargin: Style.xl
                        }
                        spacing: Style.md

                        ColumnLayout {
                            spacing: 1
                            Text {
                                text: root.selectedProject.length > 0 ? root.selectedProject : "No project selected"
                                color: Style.textPrimary
                                font.pixelSize: Style.fontXl
                                font.bold: true
                            }
                            Text {
                                text: contextModel.filteredContexts(root.selectedProject).length + " contexts"
                                color: Style.textSecondary
                                font.pixelSize: Style.fontSm
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        // Context actions
                        CardButton {
                            icon: "+"
                            label: "New Context"
                            accent: true
                            onClicked: editorDlg.open()
                        }
                    }
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 1
                        color: Style.border
                    }
                }

                // Context cards grid
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    Flickable {
                        contentWidth: width
                        contentHeight: cardsFlow_.implicitHeight + Style.xl * 2

                        Flow {
                            id: cardsFlow_
                            x: Style.xl
                            y: Style.xl
                            width: parent.width - Style.xl * 2
                            spacing: Style.lg

                            Repeater {
                                model: contextModel.filteredContexts(root.selectedProject)

                                ContextCard {
                                    contextName: modelData.name
                                    projectName: modelData.project
                                    description: modelData.description
                                    launchTarget: modelData.launchTarget
                                    packages: modelData.packages

                                    onEditInfoRequested: {
                                        editorDlg.contextNameValue = modelData.name;
                                        editorDlg.open();
                                    }
                                    onEditPackagesRequested: {
                                        pkgManagerWin.contextName_ = modelData.name;
                                        pkgManagerWin.projectName_ = modelData.project;
                                        pkgManagerWin.show();
                                    }
                                    onPreviewRequested: {
                                        previewWin.contextName_ = modelData.name;
                                        previewWin.projectName_ = modelData.project;
                                        previewWin.show();
                                    }
                                    onLaunchRequested: {
                                        launchToast_.projectName = modelData.project;
                                        launchToast_.contextName = modelData.name;
                                        launchToast_.show();
                                    }
                                }
                            }

                            // Empty state
                            Rectangle {
                                visible: contextModel.filteredContexts(root.selectedProject).length === 0
                                width: 300
                                height: 160
                                radius: Style.radiusLg
                                color: "transparent"
                                border.width: 1
                                border.color: Style.border

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: Style.md
                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: "⊞"
                                        font.pixelSize: 36
                                        color: Style.textDisabled
                                    }
                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: "No contexts yet"
                                        color: Style.textSecondary
                                        font.pixelSize: Style.fontLg
                                        font.bold: true
                                    }
                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: "Create your first context to get started."
                                        color: Style.textDisabled
                                        font.pixelSize: Style.fontMd
                                    }
                                    CardButton {
                                        Layout.alignment: Qt.AlignHCenter
                                        label: "New Context"
                                        accent: true
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
            visible = true;
            hideTimer_.restart();
        }

        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: Style.xl
        }
        width: toastRow_.implicitWidth + Style.xl
        height: 44
        radius: Style.radius
        color: Style.elevated
        border.width: 1
        border.color: Style.borderBright
        visible: false
        opacity: visible ? 1.0 : 0.0
        Behavior on opacity {
            NumberAnimation {
                duration: 200
            }
        }

        Timer {
            id: hideTimer_
            interval: 3000
            onTriggered: launchToast_.visible = false
        }

        Row {
            id: toastRow_
            anchors.centerIn: parent
            spacing: Style.sm
            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: Style.success
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "Launching: " + launchToast_.projectName + " / " + launchToast_.contextName
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
            }
        }
    }
}
