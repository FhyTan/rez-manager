import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager 1.0
import "components"
import "windows"

ApplicationWindow {
    id: root
    title: "rez-manager"
    width: 1080
    height: 760
    minimumWidth: 960
    minimumHeight: 600
    visible: true
    color: Style.bg

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
        projectOptions: projectModel.projectNames
        onSaveRequested: function(originalProjectName, originalContextName, projectName, contextName, description, launchTarget, customCommand, packages) {
            const saved = contextModel.saveContext(
                originalProjectName,
                originalContextName,
                projectName,
                contextName,
                description,
                launchTarget,
                customCommand,
                packages
            );
            if (saved) {
                editorDlg.close();
                root.selectProjectByName(projectName);
                root.showStatus("Saved context: " + projectName + " / " + contextName, false);
            } else {
                root.showStatus(contextModel.lastError, true);
            }
        }
    }
    ProjectNameDialog {
        id: projectNameDlg
        anchors.centerIn: root.contentItem
        onSubmitted: function(projectName) {
            let success = false;
            if (root.projectDialogMode === "create")
                success = projectModel.createProject(projectName);
            else if (root.projectDialogMode === "edit")
                success = projectModel.renameProject(root.projectDialogSourceName, projectName);
            else if (root.projectDialogMode === "duplicate")
                success = projectModel.duplicateProject(root.projectDialogSourceName, projectName);

            if (success) {
                projectNameDlg.close();
                contextModel.reload();
                root.selectProjectByName(projectName);
                root.showStatus("Saved project: " + projectName, false);
            } else {
                root.showStatus(projectModel.lastError, true);
            }
        }
    }
    ContextDuplicateDialog {
        id: contextDuplicateDlg
        anchors.centerIn: root.contentItem
        projectOptions: projectModel.projectNames
        onSubmitted: function(projectName, contextName) {
            const duplicated = contextModel.duplicateContext(
                root.duplicateSourceProjectName,
                root.duplicateSourceContextName,
                projectName,
                contextName
            );
            if (duplicated) {
                contextDuplicateDlg.close();
                root.selectProjectByName(projectName);
                root.showStatus("Duplicated context: " + projectName + " / " + contextName, false);
            } else {
                root.showStatus(contextModel.lastError, true);
            }
        }
    }
    ConfirmDeleteDialog {
        id: confirmDeleteDlg
        anchors.centerIn: root.contentItem
        onConfirmed: {
            if (root.pendingDeleteKind === "project") {
                if (projectModel.deleteProject(root.pendingDeleteProjectName)) {
                    contextModel.reload();
                    root.clampSelectedProjectIndex();
                    root.showStatus("Deleted project: " + root.pendingDeleteProjectName, false);
                } else {
                    root.showStatus(projectModel.lastError, true);
                }
            } else if (root.pendingDeleteKind === "context") {
                if (contextModel.deleteContext(root.pendingDeleteProjectName, root.pendingDeleteContextName)) {
                    root.showStatus(
                        "Deleted context: "
                            + root.pendingDeleteProjectName
                            + " / "
                            + root.pendingDeleteContextName,
                        false
                    );
                } else {
                    root.showStatus(contextModel.lastError, true);
                }
            }
        }
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
    property string selectedProject: selectedProjectIndex >= 0 && selectedProjectIndex < projectModel.count ? (projectModel.get(selectedProjectIndex).name || "") : ""
    property string projectDialogMode: "create"
    property string projectDialogSourceName: ""
    property string duplicateSourceProjectName: ""
    property string duplicateSourceContextName: ""
    property string pendingDeleteKind: ""
    property string pendingDeleteProjectName: ""
    property string pendingDeleteContextName: ""

    function clampSelectedProjectIndex() {
        if (projectModel.count === 0) {
            selectedProjectIndex = 0;
            return;
        }
        if (selectedProjectIndex < 0)
            selectedProjectIndex = 0;
        else if (selectedProjectIndex >= projectModel.count)
            selectedProjectIndex = projectModel.count - 1;
    }

    function selectProjectByName(projectName) {
        const targetIndex = projectModel.indexOfProject(projectName);
        if (targetIndex >= 0)
            selectedProjectIndex = targetIndex;
        else
            clampSelectedProjectIndex();
    }

    function showStatus(message, isError) {
        statusToast_.show(message, isError ? Style.error : Style.success);
    }

    function openCreateProjectDialog() {
        projectDialogMode = "create";
        projectDialogSourceName = "";
        projectNameDlg.title = "New Project";
        projectNameDlg.projectNameValue = "";
        projectNameDlg.open();
    }

    function openEditProjectDialog(projectName) {
        projectDialogMode = "edit";
        projectDialogSourceName = projectName;
        projectNameDlg.title = "Edit Project";
        projectNameDlg.projectNameValue = projectName;
        projectNameDlg.open();
    }

    function openDuplicateProjectDialog(projectName) {
        projectDialogMode = "duplicate";
        projectDialogSourceName = projectName;
        projectNameDlg.title = "Duplicate Project";
        projectNameDlg.projectNameValue = projectName + " Copy";
        projectNameDlg.open();
    }

    function openNewContextDialog() {
        if (selectedProject.length === 0) {
            showStatus("Create a project first.", true);
            return;
        }
        editorDlg.title = "New Context";
        editorDlg.originalProjectValue = "";
        editorDlg.originalContextNameValue = "";
        editorDlg.projectValue = selectedProject;
        editorDlg.contextNameValue = "";
        editorDlg.descriptionValue = "";
        editorDlg.launchTargetValue = "shell";
        editorDlg.customCommandValue = "";
        editorDlg.packagesValue = [];
        editorDlg.open();
    }

    function openEditContextDialog(modelData) {
        editorDlg.title = "Edit Context";
        editorDlg.originalProjectValue = modelData.project;
        editorDlg.originalContextNameValue = modelData.name;
        editorDlg.projectValue = modelData.project;
        editorDlg.contextNameValue = modelData.name;
        editorDlg.descriptionValue = modelData.description;
        editorDlg.launchTargetValue = modelData.launchTarget;
        editorDlg.customCommandValue = modelData.customCommand;
        editorDlg.packagesValue = modelData.packageRequests;
        editorDlg.open();
    }

    function openDuplicateContextDialog(modelData) {
        duplicateSourceProjectName = modelData.project;
        duplicateSourceContextName = modelData.name;
        contextDuplicateDlg.projectValue = modelData.project;
        contextDuplicateDlg.contextNameValue = modelData.name + " Copy";
        contextDuplicateDlg.open();
    }

    function confirmDeleteProject(projectName) {
        pendingDeleteKind = "project";
        pendingDeleteProjectName = projectName;
        pendingDeleteContextName = "";
        confirmDeleteDlg.title = "Delete Project";
        confirmDeleteDlg.messageText = "Delete project '" + projectName + "' and all of its contexts?";
        confirmDeleteDlg.open();
    }

    function confirmDeleteContext(projectName, contextName) {
        pendingDeleteKind = "context";
        pendingDeleteProjectName = projectName;
        pendingDeleteContextName = contextName;
        confirmDeleteDlg.title = "Delete Context";
        confirmDeleteDlg.messageText = "Delete context '" + contextName + "' from project '" + projectName + "'?";
        confirmDeleteDlg.open();
    }

    Connections {
        target: projectModel
        function onCountChanged() {
            root.clampSelectedProjectIndex();
        }
    }

    // ── Menu bar ──────────────────────────────────────────────
    menuBar: MenuBar {
        Menu {
            title: "File"
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
                        required property int index
                        required property string name
                        required property color avatarColor
                        width: ListView.view.width
                        height: 44

                        ProjectListItem {
                            anchors {
                                fill: parent
                                leftMargin: 6
                                rightMargin: 6
                            }
                            projectName: parent.name
                            avatarColor: parent.avatarColor
                            selected: root.selectedProjectIndex === parent.index
                            contextCount: {
                                contextModel.revision;
                                return contextModel.contextCountFor(parent.name);
                            }
                            onClicked: root.selectedProjectIndex = parent.index
                            onEditRequested: root.openEditProjectDialog(parent.name)
                            onDuplicateRequested: root.openDuplicateProjectDialog(parent.name)
                            onDeleteRequested: root.confirmDeleteProject(parent.name)
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
                            glyph: "+"
                            label: "Project"
                            onClicked: root.openCreateProjectDialog()
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        CardButton {
                            glyph: "⚙"
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
                                text: {
                                    contextModel.revision;
                                    return contextModel.filteredContexts(root.selectedProject).length + " contexts";
                                }
                                color: Style.textSecondary
                                font.pixelSize: Style.fontSm
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        // Context actions
                        CardButton {
                            glyph: "+"
                            label: "New Context"
                            accent: true
                            onClicked: root.openNewContextDialog()
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
                                model: {
                                    contextModel.revision;
                                    return contextModel.filteredContexts(root.selectedProject);
                                }

                                ContextCard {
                                    required property var modelData
                                    contextName: modelData.name
                                    projectName: modelData.project
                                    description: modelData.description
                                    launchTarget: modelData.launchTarget
                                    packages: modelData.packages

                                    onEditInfoRequested: {
                                        root.openEditContextDialog(modelData);
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
                                        statusToast_.show(
                                            "Launching: " + modelData.project + " / " + modelData.name,
                                            Style.success
                                        );
                                    }
                                    onDuplicateRequested: root.openDuplicateContextDialog(modelData)
                                    onDeleteRequested: root.confirmDeleteContext(modelData.project, modelData.name)
                                }
                            }

                            // Empty state
                            Rectangle {
                                visible: {
                                    contextModel.revision;
                                    return contextModel.filteredContexts(root.selectedProject).length === 0;
                                }
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
                                        onClicked: root.openNewContextDialog()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Status toast notification ──────────────────────────────
    Rectangle {
        id: statusToast_
        property string messageText: ""
        property color accentColor: Style.success

        function show(messageText, accentColor) {
            statusToast_.messageText = messageText;
            statusToast_.accentColor = accentColor;
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
            onTriggered: statusToast_.visible = false
        }

        Row {
            id: toastRow_
            anchors.centerIn: parent
            spacing: Style.sm
            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: statusToast_.accentColor
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: statusToast_.messageText
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
            }
        }
    }
}
