pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
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
    property string projectValue: "VFX Pipeline"
    property string descriptionValue: ""
    property string launchTargetValue: "shell"
    property var projectOptions: []

    padding: Style.xl
    standardButtons: Dialog.Save | Dialog.Cancel
    onAboutToShow: projectCombo_.currentIndex = Math.max(0, projectCombo_.model.indexOf(root.projectValue))
    onAccepted: root.close()
    onRejected: root.close()

    contentItem: ColumnLayout {
        spacing: Style.lg

        // ── Name ──────────────────────────────────────────────
        FormField {
            label: "Name"
            Layout.fillWidth: true
            FieldInput {
                Layout.fillWidth: true
                text: root.contextNameValue
            }
        }

        // ── Project ───────────────────────────────────────────
        FormField {
            label: "Project"
            Layout.fillWidth: true
            FieldCombo {
                id: projectCombo_
                Layout.fillWidth: true
                model: root.projectOptions.length > 0 ? root.projectOptions : [root.projectValue]
            }
        }

        // ── Description ───────────────────────────────────────
        FormField {
            label: "Description"
            Layout.fillWidth: true
            TextArea {
                Layout.fillWidth: true
                implicitHeight: 88
                text: root.descriptionValue.length > 0 ? root.descriptionValue : "A short description of this context."
                wrapMode: TextArea.WordWrap
            }
        }

        // ── Launch Target ─────────────────────────────────────
        FormField {
            label: "Launch Target"
            Layout.fillWidth: true
            RowLayout {
                spacing: Style.sm
                Repeater {
                    model: [
                        {
                            label: "Shell",
                            val: "shell",
                            col: Style.colorShell
                        },
                        {
                            label: "Maya",
                            val: "maya",
                            col: Style.colorMaya
                        },
                        {
                            label: "Houdini",
                            val: "houdini",
                            col: Style.colorHoudini
                        },
                        {
                            label: "Custom",
                            val: "custom",
                            col: Style.colorCustom
                        }
                    ]
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
                Layout.fillWidth: true
                text: "nuke -x %f"
                monospace: true
            }
        }

        // ── Thumbnail placeholder ─────────────────────────────
        FormField {
            label: "Thumbnail"
            Layout.fillWidth: true
            RowLayout {
                Rectangle {
                    width: 64
                    height: 64
                    radius: Style.radiusSm
                    color: Style.surface
                    border.width: 1
                    border.color: Style.border
                    Text {
                        anchors.centerIn: parent
                        text: "🖼"
                        font.pixelSize: 24
                    }
                }
                CardButton {
                    label: "Choose Image…"
                }
                CardButton {
                    label: "Clear"
                    danger: true
                }
            }
        }
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
