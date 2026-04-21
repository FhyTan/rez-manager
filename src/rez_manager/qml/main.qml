pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager
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
        projectModel: projectModel
    }
    PackageManagerController {
        id: packageManagerController_
    }
    ContextLauncherController {
        id: contextLauncherController_
    }
    ContextPreviewController {
        id: contextPreviewController_
    }

    // ── Sub-windows (instantiated here, shown on demand) ──────
    SettingsDialog {
        id: settingsDlg
        anchors.centerIn: root.contentItem
        onSaved: {
            root.reloadModels();
            root.showStatus("Saved settings.", false);
        }
    }
    ContextEditorDialog {
        id: editorDlg
        anchors.centerIn: root.contentItem
        projectOptions: projectModel.projectNames
        onSaveRequested: function (originalProjectName, originalContextName, projectName, contextName, description, launchTarget, customCommand, packages) {
            const saved = contextModel.saveContext(originalProjectName, originalContextName, projectName, contextName, description, launchTarget, customCommand, packages);
            if (saved) {
                editorDlg.close();
                root.selectProjectByName(projectName);
                root.showStatus("Saved context: " + projectName + " / " + contextName, false);
            }
        }
    }
    ProjectNameDialog {
        id: projectNameDlg
        anchors.centerIn: root.contentItem
        onSubmitted: function (projectName) {
            let success = false;
            if (root.projectDialogMode === "create")
                success = projectModel.createProject(projectName);
            else if (root.projectDialogMode === "edit")
                success = projectModel.renameProject(root.projectDialogSourceName, projectName);
            else if (root.projectDialogMode === "duplicate")
                success = projectModel.duplicateProject(root.projectDialogSourceName, projectName);

            if (success) {
                projectNameDlg.close();
                root.selectProjectByName(projectName);
                root.showStatus("Saved project: " + projectName, false);
            }
        }
    }
    ContextDuplicateDialog {
        id: contextDuplicateDlg
        anchors.centerIn: root.contentItem
        projectOptions: projectModel.projectNames
        onSubmitted: function (projectName, contextName) {
            const duplicated = contextModel.duplicateContext(root.duplicateSourceProjectName, root.duplicateSourceContextName, projectName, contextName);
            if (duplicated) {
                contextDuplicateDlg.close();
                root.selectProjectByName(projectName);
                root.showStatus("Duplicated context: " + projectName + " / " + contextName, false);
            }
        }
    }
    ConfirmDeleteDialog {
        id: confirmDeleteDlg
        anchors.centerIn: root.contentItem
        onConfirmed: {
            if (root.pendingDeleteKind === "project") {
                if (projectModel.deleteProject(root.pendingDeleteProjectName)) {
                    root.clampSelectedProjectIndex();
                    root.showStatus("Deleted project: " + root.pendingDeleteProjectName, false);
                }
            } else if (root.pendingDeleteKind === "context") {
                if (contextModel.deleteContext(root.pendingDeleteProjectName, root.pendingDeleteContextName)) {
                    root.showStatus("Deleted context: " + root.pendingDeleteProjectName + " / " + root.pendingDeleteContextName, false);
                }
            }
        }
    }
    PackageManagerWindow {
        id: pkgManagerWin
        visible: false
        packageManagerController: packageManagerController_
        onSaved: function (projectName, contextName) {
            contextModel.reload();
            root.showStatus("Saved packages: " + projectName + " / " + contextName, false);
        }
    }
    ContextPreviewWindow {
        id: previewWin
        visible: false
        contextPreviewController: contextPreviewController_
    }

    // ── State ─────────────────────────────────────────────────
    property int selectedProjectIndex: 0
    property string selectedProject: selectedProjectIndex >= 0 && selectedProjectIndex < projectModel.projectNames.length ? (projectModel.projectNames[selectedProjectIndex] || "") : ""
    property string projectDialogMode: "create"
    property string projectDialogSourceName: ""
    property string duplicateSourceProjectName: ""
    property string duplicateSourceContextName: ""
    property string pendingDeleteKind: ""
    property string pendingDeleteProjectName: ""
    property string pendingDeleteContextName: ""

    Component.onCompleted: contextModel.loadProject(selectedProject)
    onSelectedProjectChanged: contextModel.loadProject(selectedProject)

    function reloadModels() {
        projectModel.reload();
        clampSelectedProjectIndex();
        contextModel.reload();
    }

    function clampSelectedProjectIndex() {
        if (projectModel.projectNames.length === 0) {
            selectedProjectIndex = 0;
            return;
        }
        if (selectedProjectIndex < 0)
            selectedProjectIndex = 0;
        else if (selectedProjectIndex >= projectModel.projectNames.length)
            selectedProjectIndex = projectModel.projectNames.length - 1;
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
        if (!projectModel.ensureProjectExists(projectName))
            return;
        projectDialogMode = "edit";
        projectDialogSourceName = projectName;
        projectNameDlg.title = "Edit Project";
        projectNameDlg.projectNameValue = projectName;
        projectNameDlg.open();
    }

    function openDuplicateProjectDialog(projectName) {
        if (!projectModel.ensureProjectExists(projectName))
            return;
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
        if (!projectModel.ensureProjectExists(selectedProject))
            return;
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
        if (!contextModel.ensureContextExists(modelData.project, modelData.name))
            return;
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
        if (!contextModel.ensureContextExists(modelData.project, modelData.name))
            return;
        duplicateSourceProjectName = modelData.project;
        duplicateSourceContextName = modelData.name;
        contextDuplicateDlg.projectValue = modelData.project;
        contextDuplicateDlg.contextNameValue = modelData.name + " Copy";
        contextDuplicateDlg.open();
    }

    function confirmDeleteProject(projectName) {
        if (!projectModel.ensureProjectExists(projectName))
            return;
        pendingDeleteKind = "project";
        pendingDeleteProjectName = projectName;
        pendingDeleteContextName = "";
        confirmDeleteDlg.title = "Delete Project";
        confirmDeleteDlg.messageText = "Delete project '" + projectName + "' and all of its contexts?";
        confirmDeleteDlg.open();
    }

    function confirmDeleteContext(projectName, contextName) {
        if (!contextModel.ensureContextExists(projectName, contextName))
            return;
        pendingDeleteKind = "context";
        pendingDeleteProjectName = projectName;
        pendingDeleteContextName = contextName;
        confirmDeleteDlg.title = "Delete Context";
        confirmDeleteDlg.messageText = "Delete context '" + contextName + "' from project '" + projectName + "'?";
        confirmDeleteDlg.open();
    }

    Connections {
        target: projectModel
        function onProjectNamesChanged() {
            root.clampSelectedProjectIndex();
        }
    }

    Connections {
        target: AppErrorHub // qmllint disable unqualified
        function onErrorOccurred(message) {
            root.showStatus(message, true);
        }
    }
    Connections {
        target: contextLauncherController_
        function onLaunchSucceeded(projectName, contextName) {
            root.showStatus("Launched context: " + projectName + " / " + contextName, false);
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
            Layout.preferredWidth: 240
            color: Style.sidebar

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // App header
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 56
                    color: "transparent"

                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: Style.lg
                            rightMargin: Style.lg
                        }
                        spacing: Style.sm

                        Rectangle {
                            implicitWidth: 30
                            implicitHeight: 30
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
                    implicitHeight: 32
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
                        id: projectDelegate_
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
                            projectName: projectDelegate_.name
                            avatarColor: projectDelegate_.avatarColor
                            selected: root.selectedProjectIndex === projectDelegate_.index
                            onClicked: root.selectedProjectIndex = projectDelegate_.index
                            onEditRequested: root.openEditProjectDialog(projectDelegate_.name)
                            onDuplicateRequested: root.openDuplicateProjectDialog(projectDelegate_.name)
                            onDeleteRequested: root.confirmDeleteProject(projectDelegate_.name)
                        }
                    }
                }

                // Sidebar bottom toolbar
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 52
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
            Layout.preferredWidth: 1
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
                    implicitHeight: 56
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
                                text: contextModel.contexts.length + " contexts"
                                color: Style.textSecondary
                                font.pixelSize: Style.fontSm
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        // Context actions
                        CardButton {
                            glyph: "↻"
                            label: "Refresh"
                            onClicked: {
                                root.reloadModels();
                                root.showStatus("Refreshed projects and contexts.", false);
                            }
                        }
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
                                model: contextModel

                                delegate: Item {
                                    id: contextDelegate_
                                    required property string project
                                    required property string name
                                    required property string description
                                    required property string launchTarget
                                    required property string packages
                                    required property var packageRequests
                                    required property string customCommand

                                    width: contextCard_.width
                                    height: contextCard_.height

                                    ContextCard {
                                        id: contextCard_
                                        contextName: contextDelegate_.name
                                        projectName: contextDelegate_.project
                                        description: contextDelegate_.description
                                        launchTarget: contextDelegate_.launchTarget
                                        packages: contextDelegate_.packages

                                        onEditInfoRequested: {
                                            root.openEditContextDialog({
                                                "project": contextDelegate_.project,
                                                "name": contextDelegate_.name,
                                                "description": contextDelegate_.description,
                                                "launchTarget": contextDelegate_.launchTarget,
                                                "packages": contextDelegate_.packages,
                                                "packageRequests": contextDelegate_.packageRequests,
                                                "customCommand": contextDelegate_.customCommand
                                            });
                                        }
                                        onEditPackagesRequested: {
                                            if (!contextModel.ensureContextExists(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            if (!pkgManagerWin.loadContext(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            pkgManagerWin.show();
                                            pkgManagerWin.requestActivate();
                                        }
                                        onPreviewRequested: {
                                            if (!contextModel.ensureContextExists(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            if (!contextPreviewController_.loadContext(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            previewWin.show();
                                            previewWin.requestActivate();
                                        }
                                        onLaunchRequested: {
                                            if (!contextModel.ensureContextExists(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            if (!contextLauncherController_.launchContext(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            root.showStatus("Launching context: " + contextDelegate_.project + " / " + contextDelegate_.name, false);
                                        }
                                        onDuplicateRequested: root.openDuplicateContextDialog({
                                            "project": contextDelegate_.project,
                                            "name": contextDelegate_.name
                                        })
                                        onDeleteRequested: root.confirmDeleteContext(contextDelegate_.project, contextDelegate_.name)
                                    }
                                }
                            }

                            // Empty state
                            Rectangle {
                                visible: contextModel.contexts.length === 0
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
