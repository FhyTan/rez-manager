import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."
import "../components"

// Context editor dialog — create or edit a context's metadata.
Dialog {
    id: root
    title: "Edit Context"
    modal: true
    width:  520
    height: 520

    property string contextNameValue:  "New Context"
    property string projectValue:      "VFX Pipeline"
    property string descriptionValue:  ""
    property string launchTargetValue: "shell"

    padding: Style.xl
    standardButtons: Dialog.Save | Dialog.Cancel
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
                Layout.fillWidth: true
                model: ["VFX Pipeline", "Maya Rigging", "Houdini FX", "USD Pipeline"]
                currentIndex: 0
            }
        }

        // ── Description ───────────────────────────────────────
        FormField {
            label: "Description"
            Layout.fillWidth: true
            TextArea {
                Layout.fillWidth: true
                implicitHeight: 88
                text: root.descriptionValue.length > 0
                    ? root.descriptionValue
                    : "A short description of this context."
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
                        { label: "Shell",   val: "shell",   col: Style.colorShell   },
                        { label: "Maya",    val: "maya",    col: Style.colorMaya    },
                        { label: "Houdini", val: "houdini", col: Style.colorHoudini },
                        { label: "Custom",  val: "custom",  col: Style.colorCustom  }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        height: 32; width: selLbl_.implicitWidth + 24
                        radius: Style.radiusSm
                        property bool isSelected: root.launchTargetValue === modelData.val
                        color: isSelected
                            ? Qt.rgba(modelData.col.r, modelData.col.g, modelData.col.b, 0.15)
                            : (selHov_.hovered ? Qt.rgba(1,1,1,0.04) : "transparent")
                        border.width: 1
                        border.color: isSelected
                            ? Qt.rgba(modelData.col.r, modelData.col.g, modelData.col.b, 0.5)
                            : Style.border
                        Behavior on color { ColorAnimation { duration: 80 } }
                        Text {
                            id: selLbl_
                            anchors.centerIn: parent
                            text:           modelData.label
                            color:          isSelected ? modelData.col : Style.textSecondary
                            font.pixelSize: Style.fontMd
                            font.bold:      isSelected
                        }
                        HoverHandler { id: selHov_; cursorShape: Qt.PointingHandCursor }
                        TapHandler {
                            acceptedButtons: Qt.LeftButton
                            onTapped: root.launchTargetValue = modelData.val
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
                    width: 64; height: 64; radius: Style.radiusSm
                    color: Style.surface; border.width: 1; border.color: Style.border
                    Text { anchors.centerIn: parent; text: "🖼"; font.pixelSize: 24 }
                }
                CardButton { label: "Choose Image…" }
                CardButton { label: "Clear"; danger: true }
            }
        }
    }

    // Inline helper components ────────────────────────────────
    component FormField: ColumnLayout {
        property string label: ""
        default property alias content: contentHolder_.data
        spacing: Style.xs
        Text {
            text:           parent.label
            color:          Style.textSecondary
            font.pixelSize: Style.fontSm
        }
        ColumnLayout { id: contentHolder_; spacing: 0 }
    }

    component FieldInput: TextField {
        property bool  monospace: false
        implicitHeight: 36
        font.pixelSize: Style.fontMd
        font.family: monospace ? "Consolas, Courier New, monospace" : font.family
        selectByMouse: true
    }

    component FieldCombo: ComboBox {
        implicitHeight: 36
    }
}
