pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import ".."
import "../components"

// Context editor dialog — create or edit a context's metadata.
Dialog {
    id: root
    title: "Edit Context"
    modal: true
    width: 520
    height: Math.max(520, implicitHeight)

    property string contextNameValue: "New Context"
    property string originalContextNameValue: ""
    property string projectValue: "VFX Pipeline"
    property string originalProjectValue: ""
    property string descriptionValue: ""
    property string launchTargetValue: "shell"
    property string customCommandValue: ""
    property url thumbnailSourceValue: ""
    property var packagesValue: []
    property var projectOptions: []
    signal saveRequested(string originalProjectName, string originalContextName, string projectName, string contextName, string description, string launchTarget, string customCommand, var packages)
    readonly property var launchTargetOptions: [
        {
            label: "Shell",
            val: "shell",
            col: Style.colorShell,
            iconName: "Shell"
        },
        {
            label: "Maya",
            val: "maya",
            col: Style.colorMaya,
            iconName: "Maya"
        },
        {
            label: "Houdini",
            val: "houdini",
            col: Style.colorHoudini,
            iconName: "Houdini"
        },
        {
            label: "Blender",
            val: "blender",
            col: Style.colorBlender,
            iconName: "Blender"
        },
        {
            label: "Nuke",
            val: "nuke",
            col: Style.colorNuke,
            iconName: "Nuke"
        },
        {
            label: "NukeX",
            val: "nukex",
            col: Style.colorNukeX,
            iconName: "NukeX"
        },
        {
            label: "Custom",
            val: "custom",
            col: Style.colorCustom,
            iconName: ""
        }
    ]
    readonly property string selectedTargetIconSource: {
        const targetOption = root.launchTargetOption(root.launchTargetValue);
        if (targetOption === null || targetOption.iconName.length === 0)
            return "";
        return "qrc:/icons/dcc/" + targetOption.iconName;
    }

    function comboProjectOptions() {
        if (root.projectValue.length === 0)
            return root.projectOptions;
        if (root.projectOptions.indexOf(root.projectValue) >= 0)
            return root.projectOptions;
        return [root.projectValue].concat(root.projectOptions);
    }

    function launchTargetOption(targetValue) {
        for (let index = 0; index < root.launchTargetOptions.length; index++) {
            const targetOption = root.launchTargetOptions[index];
            if (targetOption.val === targetValue)
                return targetOption;
        }
        return null;
    }

    padding: Style.xl
    standardButtons: Dialog.Save | Dialog.Cancel
    onAboutToShow: {
        projectNameField_.text = root.contextNameValue;
        const projectIndex = projectCombo_.model.indexOf(root.projectValue);
        projectCombo_.currentIndex = projectIndex >= 0 ? projectIndex : 0;
        descriptionField_.text = root.descriptionValue;
        customCommandField_.text = root.customCommandValue;
        root.thumbnailSourceValue = "";
    }
    onAccepted: {
        root.saveRequested(root.originalProjectValue, root.originalContextNameValue, projectCombo_.currentText, projectNameField_.text, descriptionField_.text, root.launchTargetValue, customCommandField_.text, root.packagesValue);
    }
    onRejected: root.close()

    contentItem: ColumnLayout {
        spacing: Style.lg

        // ── Name ──────────────────────────────────────────────
        FormField {
            label: "Name"
            Layout.fillWidth: true
            FieldInput {
                id: projectNameField_
                Layout.fillWidth: true
            }
        }

        // ── Project ───────────────────────────────────────────
        FormField {
            label: "Project"
            Layout.fillWidth: true
            FieldCombo {
                id: projectCombo_
                Layout.fillWidth: true
                model: root.comboProjectOptions()
            }
        }

        // ── Description ───────────────────────────────────────
        FormField {
            label: "Description"
            Layout.fillWidth: true
            TextArea {
                id: descriptionField_
                Layout.fillWidth: true
                implicitHeight: 88
                placeholderText: "A short description of this context."
                wrapMode: TextArea.WordWrap
            }
        }

        // ── Launch Target ─────────────────────────────────────
        FormField {
            label: "Launch Target"
            Layout.fillWidth: true
            Flow {
                Layout.fillWidth: true
                width: parent.width
                spacing: Style.sm
                Repeater {
                    model: root.launchTargetOptions
                    delegate: Rectangle {
                        id: launchOption_
                        required property var modelData
                        height: 32
                        width: selLbl_.implicitWidth + 24
                        radius: Style.radiusSm
                        property bool isSelected: root.launchTargetValue === launchOption_.modelData.val
                        color: launchOption_.isSelected ? Qt.rgba(launchOption_.modelData.col.r, launchOption_.modelData.col.g, launchOption_.modelData.col.b, 0.15) : (selHov_.hovered ? Qt.rgba(1, 1, 1, 0.04) : "transparent")
                        border.width: 1
                        border.color: launchOption_.isSelected ? Qt.rgba(launchOption_.modelData.col.r, launchOption_.modelData.col.g, launchOption_.modelData.col.b, 0.5) : Style.border
                        Behavior on color {
                            ColorAnimation {
                                duration: 80
                            }
                        }
                        Text {
                            id: selLbl_
                            anchors.centerIn: parent
                            text: launchOption_.modelData.label
                            color: launchOption_.isSelected ? launchOption_.modelData.col : Style.textSecondary
                            font.pixelSize: Style.fontMd
                            font.bold: launchOption_.isSelected
                        }
                        HoverHandler {
                            id: selHov_
                            cursorShape: Qt.PointingHandCursor
                        }
                        TapHandler {
                            acceptedButtons: Qt.LeftButton
                            gesturePolicy: TapHandler.WithinBounds
                            onTapped: root.launchTargetValue = launchOption_.modelData.val
                        }
                    }
                }
            }
        }

        // Custom command (shown when launchTarget = custom)
        FormField {
            label: "Custom Command"
            Layout.fillWidth: true
            visible: root.launchTargetValue === "custom"
            FieldInput {
                id: customCommandField_
                Layout.fillWidth: true
                monospace: true
                placeholderText: "nuke -x %f"
            }
        }

        // ── Thumbnail placeholder ─────────────────────────────
        FormField {
            label: "Thumbnail"
            Layout.fillWidth: true
            RowLayout {
                Layout.fillWidth: true
                Rectangle {
                    implicitWidth: 64
                    implicitHeight: 64
                    radius: Style.radiusSm
                    color: Style.surface
                    border.width: 1
                    border.color: Style.border
                    Image {
                        anchors.fill: parent
                        anchors.margins: Style.sm
                        fillMode: Image.PreserveAspectFit
                        source: root.thumbnailSourceValue
                        visible: root.thumbnailSourceValue.toString().length > 0
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "🖼"
                        font.pixelSize: 24
                        visible: root.thumbnailSourceValue.toString().length === 0
                    }
                }
                CardButton {
                    label: "Choose Image…"
                    onClicked: thumbnailDialog_.open()
                }
                CardButton {
                    label: "Add Target Icon"
                    enabled: root.selectedTargetIconSource.length > 0
                    onClicked: root.thumbnailSourceValue = root.selectedTargetIconSource
                }
                CardButton {
                    label: "Clear"
                    danger: true
                    enabled: root.thumbnailSourceValue.toString().length > 0
                    onClicked: root.thumbnailSourceValue = ""
                }
            }
        }
    }

    FileDialog {
        id: thumbnailDialog_
        title: "Choose Thumbnail"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Image files (*.png *.jpg *.jpeg *.bmp *.svg *.webp)", "All files (*)"]
        onAccepted: root.thumbnailSourceValue = thumbnailDialog_.selectedFile
    }

    // Inline helper components ────────────────────────────────
    component FormField: ColumnLayout {
        id: formField_
        property string label: ""
        default property alias content: contentHolder_.data
        spacing: Style.xs
        Text {
            text: formField_.label
            color: Style.textSecondary
            font.pixelSize: Style.fontSm
        }
        ColumnLayout {
            id: contentHolder_
            spacing: 0
        }
    }

    component FieldInput: TextField {
        property bool monospace: false
        implicitHeight: 36
        font.pixelSize: Style.fontMd
        font.family: monospace ? "Consolas, Courier New, monospace" : font.family
        selectByMouse: true
    }

    component FieldCombo: ComboBox {
        implicitHeight: 36
    }
}
