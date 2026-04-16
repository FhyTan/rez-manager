pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import RezManager
import ".."
import "../components"

// Settings dialog — configure repositories and contexts location.
Dialog {
    id: root
    title: "Settings"
    modal: true
    width: 620
    height: parent ? Math.max(520, Math.min(620, parent.height - Style.xl * 2)) : 560
    padding: Style.xl
    property var packageRepositoriesValue: []
    property string contextMenuRepositoryPath: ""
    signal saved
    onAboutToShow: {
        settingsController_.reload();
        root.packageRepositoriesValue = settingsController_.packageRepositories;
        contextsLocationField_.text = settingsController_.contextsLocation;
    }

    function addRepository(path) {
        const normalizedPath = settingsController_.normalizeRepositoryPath(path);
        if (normalizedPath.length === 0)
            return;

        const nextIdentity = settingsController_.repositoryIdentity(normalizedPath);
        for (const existingPath of root.packageRepositoriesValue) {
            if (settingsController_.repositoryIdentity(existingPath) === nextIdentity)
                return;
        }

        const nextRepositories = root.packageRepositoriesValue.slice();
        nextRepositories.push(normalizedPath);
        root.packageRepositoriesValue = nextRepositories;
    }

    function removeRepository(index) {
        if (index < 0 || index >= root.packageRepositoriesValue.length)
            return;

        const nextRepositories = root.packageRepositoriesValue.slice();
        nextRepositories.splice(index, 1);
        root.packageRepositoriesValue = nextRepositories;
    }

    function importSettings(path) {
        if (!settingsController_.importFromFile(path))
            return;

        root.syncFromController();
    }

    function saveSettings() {
        if (!settingsController_.save(root.packageRepositoriesValue, contextsLocationField_.text))
            return;

        root.saved();
        root.close();
    }

    function exportSettings(path) {
        if (!settingsController_.exportToFile(root.packageRepositoriesValue, contextsLocationField_.text, path))
            return;

        root.syncFromController();
    }

    function syncFromController() {
        root.packageRepositoriesValue = settingsController_.packageRepositories;
        contextsLocationField_.text = settingsController_.contextsLocation;
    }

    function copyText(text) {
        clipboardProxy_.text = text;
        clipboardProxy_.selectAll();
        clipboardProxy_.copy();
        clipboardProxy_.deselect();
    }

    function openRepositoryMenu(path, item, point) {
        root.contextMenuRepositoryPath = path;
        repositoryMenu_.popup(item, point.x, point.y);
    }

    AppSettingsController {
        id: settingsController_
    }

    TextEdit {
        id: clipboardProxy_
        visible: false
    }

    FolderDialog {
        id: repoFolderDialog_
        currentFolder: selectedFolder
        onAccepted: root.addRepository(settingsController_.pathFromUrl(repoFolderDialog_.selectedFolder.toString()))
    }

    FolderDialog {
        id: contextsFolderDialog_
        currentFolder: selectedFolder
        onAccepted: contextsLocationField_.text = settingsController_.pathFromUrl(contextsFolderDialog_.selectedFolder.toString())
    }

    FileDialog {
        id: importSettingsDialog_
        title: qsTr("Import Settings")
        fileMode: FileDialog.OpenFile
        nameFilters: [qsTr("JSON files (*.json)"), qsTr("All files (*)")]
        onAccepted: root.importSettings(settingsController_.pathFromUrl(importSettingsDialog_.selectedFile.toString()))
    }

    FileDialog {
        id: exportSettingsDialog_
        title: qsTr("Export Settings")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        nameFilters: [qsTr("JSON files (*.json)"), qsTr("All files (*)")]
        onAccepted: root.exportSettings(settingsController_.pathFromUrl(exportSettingsDialog_.selectedFile.toString()))
    }

    contentItem: ScrollView {
        id: contentScroll_
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: contentScroll_.availableWidth - contentScroll_.effectiveScrollBarWidth 
            spacing: Style.xl

            // ── Package Repositories ───────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Style.sm

                Text {
                    text: "Package Repositories"
                    color: Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold: true
                }
                Text {
                    text: "Each folder is treated as a named package group."
                    color: Style.textSecondary
                    font.pixelSize: Style.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }

                // Repo list
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 220
                    radius: Style.radius
                    color: Style.surface
                    border.width: 1
                    border.color: Style.border
                    clip: true

                    ListView {
                        id: repositoriesList_
                        anchors {
                            fill: parent
                            margins: Style.sm
                        }
                        model: root.packageRepositoriesValue
                        spacing: 2
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: ScrollBar {}

                        delegate: Rectangle {
                            id: repoRow_
                            required property string modelData
                            required property int index
                            width: repositoriesList_.width
                            height: 38
                            radius: Style.radiusSm
                            color: repoHover_.hovered ? Style.elevated : "transparent"

                            Behavior on color {
                                ColorAnimation {
                                    duration: 80
                                }
                            }

                            RowLayout {
                                anchors {
                                    fill: parent
                                    leftMargin: Style.md
                                    rightMargin: Style.sm
                                }
                                spacing: Style.sm

                                Rectangle {
                                    width: 6
                                    height: 6
                                    radius: 3
                                    color: Style.accent
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: repoRow_.modelData
                                    color: Style.textPrimary
                                    font.pixelSize: Style.fontMd
                                    font.family: "Consolas, Courier New, monospace"
                                    elide: Text.ElideLeft
                                }
                                CardButton {
                                    glyph: "✕"
                                    danger: true
                                    square: true
                                    implicitHeight: 26
                                    minimumWidth: 26
                                    onClicked: root.removeRepository(repoRow_.index)
                                }
                            }
                            HoverHandler {
                                id: repoHover_
                            }
                            TapHandler {
                                acceptedButtons: Qt.RightButton
                                gesturePolicy: TapHandler.WithinBounds
                                onTapped: function (eventPoint) {
                                    root.openRepositoryMenu(repoRow_.modelData, repoRow_, eventPoint.position);
                                }
                            }
                        }

                        Text {
                            anchors.centerIn: parent
                            visible: repositoriesList_.count === 0
                            text: qsTr("No repositories configured.")
                            color: Style.textSecondary
                            font.pixelSize: Style.fontMd
                        }
                    }
                }

                // Add repo row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.sm

                    Item {
                        Layout.fillWidth: true
                    }
                    CardButton {
                        id: addRepoButton_
                        label: qsTr("Add…")
                        onClicked: repoFolderDialog_.open()
                    }
                }
            }

            // ── Contexts Location ──────────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Style.sm

                Text {
                    text: "Contexts Location"
                    color: Style.textPrimary
                    font.pixelSize: Style.fontLg
                    font.bold: true
                }
                Text {
                    text: "Root directory where project/context data is stored on disk."
                    color: Style.textSecondary
                    font.pixelSize: Style.fontMd
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.sm
                    TextField {
                        id: contextsLocationField_
                        Layout.fillWidth: true
                    }
                    CardButton {
                        label: "Browse…"
                        onClicked: contextsFolderDialog_.open()
                    }
                }
            }
        }
    }

    footer: Rectangle {
        implicitHeight: footerLayout_.implicitHeight + Style.lg * 2 + 1
        color: "transparent"

        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: Style.border
        }

        RowLayout {
            id: footerLayout_
            anchors {
                fill: parent
                leftMargin: Style.lg
                rightMargin: Style.lg
                topMargin: Style.lg + 1
                bottomMargin: Style.lg
            }
            spacing: Style.sm

            RowLayout {
                spacing: Style.sm

                Button {
                    text: qsTr("Import")
                    onClicked: importSettingsDialog_.open()
                }
                Button {
                    text: qsTr("Export")
                    onClicked: exportSettingsDialog_.open()
                }
            }

            Item {
                Layout.fillWidth: true
            }

            RowLayout {
                spacing: Style.sm

                Button {
                    text: qsTr("Cancel")
                    onClicked: root.close()
                }
                Button {
                    text: qsTr("Save")
                    highlighted: true
                    onClicked: root.saveSettings()
                }
            }
        }
    }

    Menu {
        id: repositoryMenu_

        MenuItem {
            text: qsTr("Copy To Clipboard")
            enabled: root.contextMenuRepositoryPath.length > 0
            onTriggered: root.copyText(root.contextMenuRepositoryPath)
        }
        MenuItem {
            text: qsTr("Reveal in File Explorer")
            enabled: root.contextMenuRepositoryPath.length > 0
            onTriggered: settingsController_.revealInFileExplorer(root.contextMenuRepositoryPath)
        }
    }
}
