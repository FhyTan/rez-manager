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

    background: Rectangle {
        color:        Style.elevated
        radius:       Style.radiusLg
        border.width: 1
        border.color: Style.borderBright
    }

    header: Rectangle {
        height: 56; color: "transparent"
        RowLayout {
            anchors { fill: parent; leftMargin: Style.xl; rightMargin: Style.lg }
            Text {
                text:           root.contextNameValue.length > 0 ? "Edit Context" : "New Context"
                color:          Style.textPrimary
                font.pixelSize: Style.fontXl
                font.bold:      true
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                width: 28; height: 28; radius: 14
                color: xHov_.containsMouse ? Style.border : "transparent"
                Text { anchors.centerIn: parent; text: "✕"; color: Style.textSecondary; font.pixelSize: Style.fontMd }
                MouseArea { id: xHov_; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
            }
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Style.border }
    }

    footer: Rectangle {
        height: 56; color: "transparent"
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Style.border }
        RowLayout {
            anchors { fill: parent; leftMargin: Style.xl; rightMargin: Style.xl }
            Item { Layout.fillWidth: true }
            CardButton { label: "Cancel"; onClicked: root.close() }
            Item { width: Style.sm }
            CardButton { label: "Save"; accent: true; onClicked: root.close() }
        }
    }


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
            Rectangle {
                Layout.fillWidth: true
                height: 72; radius: Style.radiusSm
                color: Style.surface; border.width: 1; border.color: Style.border
                TextArea {
                    anchors.fill: parent
                    leftPadding: Style.md; rightPadding: Style.md
                    topPadding: Style.sm; bottomPadding: Style.sm
                    text:            root.descriptionValue.length > 0 ? root.descriptionValue : "A short description of this context."
                    color:           Style.textPrimary
                    font.pixelSize:  Style.fontMd
                    wrapMode:        TextArea.WordWrap
                    background: null
                }
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
                            : (selHov_.containsMouse ? Qt.rgba(1,1,1,0.04) : "transparent")
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
                        MouseArea {
                            id: selHov_; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.launchTargetValue = modelData.val
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

    component FieldInput: Rectangle {
        property alias text:     ti_.text
        property bool  monospace: false
        height: 36; radius: Style.radiusSm
        color: Style.surface; border.width: 1; border.color: Style.border
        TextInput {
            id: ti_
            anchors.left: parent.left; anchors.right: parent.right
            anchors.leftMargin: Style.md; anchors.rightMargin: Style.md
            anchors.verticalCenter: parent.verticalCenter
            color:           Style.textPrimary
            font.pixelSize:  Style.fontMd
            font.family:     monospace ? "Consolas, Courier New, monospace" : font.family
            selectByMouse:   true
        }
    }

    component FieldCombo: ComboBox {
        height: 36
        background: Rectangle {
            color: Style.surface; radius: Style.radiusSm
            border.width: 1; border.color: Style.border
        }
        contentItem: Text {
            leftPadding: Style.md
            text:            parent.displayText
            color:           Style.textPrimary
            font.pixelSize:  Style.fontMd
            verticalAlignment: Text.AlignVCenter
        }
        popup: Popup {
            y: parent.height + 4
            width: parent.width
            background: Rectangle {
                color: Style.elevated; radius: Style.radiusSm
                border.width: 1; border.color: Style.borderBright
            }
            contentItem: ListView {
                implicitHeight: Math.min(contentHeight, 200)
                model: parent.parent.delegateModel
                clip: true
                ScrollIndicator.vertical: ScrollIndicator {}
            }
        }
        delegate: ItemDelegate {
            width: parent ? parent.width : 0
            height: 36
            background: Rectangle {
                color: parent.hovered ? Style.elevated : "transparent"
            }
            contentItem: Text {
                leftPadding:     Style.md
                text:            modelData
                color:           Style.textPrimary
                font.pixelSize:  Style.fontMd
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
