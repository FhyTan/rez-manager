pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager
import RezManager.Components
import RezManager.Windows

ApplicationWindow {
    id: root
    title: "rez-manager"
    width: 1080
    height: 760
    minimumWidth: 960
    minimumHeight: 600
    visible: true
    color: Style.bg
    readonly property string errorTarget_: "main"
    AppErrorTarget.errorTarget: root.errorTarget_

    ProjectListModel {
        id: projectModel_
    }
    RezContextListModel {
        id: contextModel_
        projectModel: projectModel_
    }
    LaunchTargetListModel {
        id: launchTargetModel_
    }
    ContextLauncherController {
        id: contextLauncherController_
    }
    ContextPreviewController {
        id: contextPreviewController_
    }
    LogViewerController {
        id: logViewerController_
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
        launchTargetModel: launchTargetModel_
        projectOptions: projectModel_.projectNames
        onSaveRequested: function (originalProjectName, originalContextName, projectName, contextName, description, launchTarget, customCommand, builtinThumbnailSource, thumbnailSource, packages) {
            const saved = contextModel_.saveContext(originalProjectName, originalContextName, projectName, contextName, description, launchTarget, customCommand, builtinThumbnailSource, thumbnailSource, packages);
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
                success = projectModel_.createProject(projectName);
            else if (root.projectDialogMode === "edit")
                success = projectModel_.renameProject(root.projectDialogSourceName, projectName);
            else if (root.projectDialogMode === "duplicate")
                success = projectModel_.duplicateProject(root.projectDialogSourceName, projectName);

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
        projectOptions: projectModel_.projectNames
        onSubmitted: function (projectName, contextName) {
            const duplicated = contextModel_.duplicateContext(root.duplicateSourceProjectName, root.duplicateSourceContextName, projectName, contextName);
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
                if (projectModel_.deleteProject(root.pendingDeleteProjectName)) {
                    root.clampSelectedProjectIndex();
                    root.showStatus("Deleted project: " + root.pendingDeleteProjectName, false);
                }
            } else if (root.pendingDeleteKind === "context") {
                if (contextModel_.deleteContext(root.pendingDeleteProjectName, root.pendingDeleteContextName)) {
                    root.showStatus("Deleted context: " + root.pendingDeleteProjectName + " / " + root.pendingDeleteContextName, false);
                }
            }
        }
    }
    AboutDialog {
        id: aboutDlg
        anchors.centerIn: root.contentItem
        onGithubRequested: root.openGithubPage()
    }
    PackageManagerWindow {
        id: pkgManagerWin
        visible: false
        onSaved: function (projectName, contextName) {
            contextModel_.reload();
            root.showStatus("Saved packages: " + projectName + " / " + contextName, false);
        }
        onOpenLogsRequested: root.openLogWindow()
    }
    ContextPreviewWindow {
        id: previewWin
        visible: false
        contextPreviewController: contextPreviewController_
    }
    LogWindow {
        id: logWin
        visible: false
        logViewerController: logViewerController_
    }

    // ── State ─────────────────────────────────────────────────
    property int selectedProjectIndex: 0
    property string selectedProject: selectedProjectIndex >= 0 && selectedProjectIndex < projectModel_.projectNames.length ? (projectModel_.projectNames[selectedProjectIndex] || "") : ""
    property string projectDialogMode: "create"
    property string projectDialogSourceName: ""
    property string duplicateSourceProjectName: ""
    property string duplicateSourceContextName: ""
    property string pendingDeleteKind: ""
    property string pendingDeleteProjectName: ""
    property string pendingDeleteContextName: ""

    Component.onCompleted: contextModel_.loadProject(selectedProject)
    onSelectedProjectChanged: contextModel_.loadProject(selectedProject)

    function reloadModels() {
        projectModel_.reload();
        clampSelectedProjectIndex();
        contextModel_.reload();
    }

    function clampSelectedProjectIndex() {
        if (projectModel_.projectNames.length === 0) {
            selectedProjectIndex = 0;
            return;
        }
        if (selectedProjectIndex < 0)
            selectedProjectIndex = 0;
        else if (selectedProjectIndex >= projectModel_.projectNames.length)
            selectedProjectIndex = projectModel_.projectNames.length - 1;
    }

    function selectProjectByName(projectName) {
        const targetIndex = projectModel_.indexOfProject(projectName);
        if (targetIndex >= 0)
            selectedProjectIndex = targetIndex;
        else
            clampSelectedProjectIndex();
    }

    function showStatus(message, isError) {
        statusToast_.show(message, isError ? Style.error : Style.success);
    }

    function openLogWindow() {
        logViewerController_.refresh();
        logWin.show();
        logWin.requestActivate();
    }

    function openImportProjectDialog() {
        showStatus(qsTr("Import Project is not implemented yet."), true);
    }

    function openImportContextDialog() {
        showStatus(qsTr("Import Context is not implemented yet."), true);
    }

    function openGithubPage() {
        if (!Qt.openUrlExternally("https://github.com/FhyTan/rez-manager"))
            showStatus(qsTr("Failed to open the GitHub page."), true);
    }

    function openAboutDialog() {
        aboutDlg.open();
    }

    function openCreateProjectDialog() {
        projectDialogMode = "create";
        projectDialogSourceName = "";
        projectNameDlg.title = "New Project";
        projectNameDlg.projectNameValue = "";
        projectNameDlg.open();
    }

    function openEditProjectDialog(projectName) {
        if (!projectModel_.ensureProjectExists(projectName))
            return;
        projectDialogMode = "edit";
        projectDialogSourceName = projectName;
        projectNameDlg.title = "Edit Project";
        projectNameDlg.projectNameValue = projectName;
        projectNameDlg.open();
    }

    function openDuplicateProjectDialog(projectName) {
        if (!projectModel_.ensureProjectExists(projectName))
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
        if (!projectModel_.ensureProjectExists(selectedProject))
            return;
        editorDlg.title = "New Context";
        editorDlg.originalProjectValue = "";
        editorDlg.originalContextNameValue = "";
        editorDlg.projectValue = selectedProject;
        editorDlg.contextNameValue = "";
        editorDlg.descriptionValue = "";
        editorDlg.launchTargetValue = launchTargetModel_.defaultValue;
        editorDlg.customCommandValue = "";
        editorDlg.builtinThumbnailSourceValue = "";
        editorDlg.thumbnailSourceValue = "";
        editorDlg.packagesValue = [];
        editorDlg.open();
    }

    function openEditContextDialog(modelData) {
        if (!contextModel_.ensureContextExists(modelData.project, modelData.name))
            return;
        editorDlg.title = "Edit Context";
        editorDlg.originalProjectValue = modelData.project;
        editorDlg.originalContextNameValue = modelData.name;
        editorDlg.projectValue = modelData.project;
        editorDlg.contextNameValue = modelData.name;
        editorDlg.descriptionValue = modelData.description;
        editorDlg.launchTargetValue = modelData.launchTarget;
        editorDlg.customCommandValue = modelData.customCommand;
        editorDlg.builtinThumbnailSourceValue = modelData.builtinThumbnailSource;
        editorDlg.thumbnailSourceValue = modelData.thumbnailSource;
        editorDlg.packagesValue = modelData.packageRequests;
        editorDlg.open();
    }

    function openDuplicateContextDialog(modelData) {
        if (!contextModel_.ensureContextExists(modelData.project, modelData.name))
            return;
        duplicateSourceProjectName = modelData.project;
        duplicateSourceContextName = modelData.name;
        contextDuplicateDlg.projectValue = modelData.project;
        contextDuplicateDlg.contextNameValue = modelData.name + " Copy";
        contextDuplicateDlg.open();
    }

    function confirmDeleteProject(projectName) {
        if (!projectModel_.ensureProjectExists(projectName))
            return;
        pendingDeleteKind = "project";
        pendingDeleteProjectName = projectName;
        pendingDeleteContextName = "";
        confirmDeleteDlg.title = "Delete Project";
        confirmDeleteDlg.messageText = "Delete project '" + projectName + "' and all of its contexts?";
        confirmDeleteDlg.open();
    }

    function confirmDeleteContext(projectName, contextName) {
        if (!contextModel_.ensureContextExists(projectName, contextName))
            return;
        pendingDeleteKind = "context";
        pendingDeleteProjectName = projectName;
        pendingDeleteContextName = contextName;
        confirmDeleteDlg.title = "Delete Context";
        confirmDeleteDlg.messageText = "Delete context '" + contextName + "' from project '" + projectName + "'?";
        confirmDeleteDlg.open();
    }

    Connections {
        target: projectModel_
        function onProjectNamesChanged() {
            root.clampSelectedProjectIndex();
        }
    }

    Connections {
        target: AppErrorHub // qmllint disable unqualified
        function onErrorOccurred(message, target) {
            if (target === root.errorTarget_ || target === "global")
                statusToast_.show(message, Style.error);
        }
    }
    Connections {
        target: contextLauncherController_
        function onLaunchSucceeded(projectName, contextName) {
            root.showStatus("Launched context: " + projectName + " / " + contextName, false);
        }
    }
    Connections {
        target: contextPreviewController_
        function onPreviewResolved() {
            previewWin.show();
            previewWin.requestActivate();
        }
    }

    // ── Menu bar ──────────────────────────────────────────────
    menuBar: MenuBar {
        Menu {
            title: qsTr("File")

            // Action {
            //     text: qsTr("Import Project")
            //     onTriggered: root.openImportProjectDialog()
            // }
            // Action {
            //     text: qsTr("Import Context")
            //     onTriggered: root.openImportContextDialog()
            // }
            // MenuSeparator {}
            Action {
                text: qsTr("Settings...")
                onTriggered: settingsDlg.open()
            }
            MenuSeparator {}
            Action {
                text: qsTr("Quit")
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: qsTr("Help")

            Action {
                text: qsTr("Open Logs")
                onTriggered: root.openLogWindow()
            }
            MenuSeparator {}
            Action {
                text: qsTr("Github")
                onTriggered: root.openGithubPage()
            }
            Action {
                text: qsTr("About")
                onTriggered: root.openAboutDialog()
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
                    model: projectModel_
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
                            RowLayout {
                                spacing: Style.sm

                                Text {
                                    text: root.selectedProject.length > 0 ? root.selectedProject : "No project selected"
                                    color: Style.textPrimary
                                    font.pixelSize: Style.fontXl
                                    font.bold: true
                                }

                                Badge {
                                    text: contextModel_.contextCount + " contexts"
                                    badgeColor: Style.accent
                                }
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
                                model: contextModel_

                                delegate: Item {
                                    id: contextDelegate_
                                    required property string project
                                    required property string name
                                    required property string description
                                    required property string launchTarget
                                    required property color launchTargetColor
                                    required property string packages
                                    required property var packageRequests
                                    required property string customCommand
                                    required property string builtinThumbnailSource
                                    required property string thumbnailSource

                                    width: contextCard_.width
                                    height: contextCard_.height

                                    ContextCard {
                                        id: contextCard_
                                        contextName: contextDelegate_.name
                                        projectName: contextDelegate_.project
                                        description: contextDelegate_.description
                                        launchTarget: contextDelegate_.launchTarget
                                        accentColor: contextDelegate_.launchTargetColor
                                        packages: contextDelegate_.packages
                                        builtinThumbnailSource: contextDelegate_.builtinThumbnailSource
                                        thumbnailSource: contextDelegate_.thumbnailSource
                                        previewBusy: contextPreviewController_.isLoading

                                        onEditInfoRequested: {
                                            root.openEditContextDialog({
                                                "project": contextDelegate_.project,
                                                "name": contextDelegate_.name,
                                                "description": contextDelegate_.description,
                                                "launchTarget": contextDelegate_.launchTarget,
                                                "packages": contextDelegate_.packages,
                                                "packageRequests": contextDelegate_.packageRequests,
                                                "customCommand": contextDelegate_.customCommand,
                                                "builtinThumbnailSource": contextDelegate_.builtinThumbnailSource,
                                                "thumbnailSource": contextDelegate_.thumbnailSource
                                            });
                                        }
                                        onEditPackagesRequested: {
                                            if (!contextModel_.ensureContextExists(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            if (!pkgManagerWin.loadContext(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            pkgManagerWin.show();
                                            pkgManagerWin.requestActivate();
                                        }
                                        onPreviewRequested: {
                                            if (!contextModel_.ensureContextExists(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            if (!contextPreviewController_.loadContext(contextDelegate_.project, contextDelegate_.name))
                                                return;
                                            statusToast_.show(qsTr("Resolving preview..."), Style.accent);
                                        }
                                        onLaunchRequested: {
                                            if (!contextModel_.ensureContextExists(contextDelegate_.project, contextDelegate_.name))
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
                                visible: contextModel_.contexts.length === 0
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
    StatusToast {
        id: statusToast_
        onActivated: root.openLogWindow()
    }
}
