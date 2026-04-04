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
        color:        s_.elevated
        radius:       s_.radiusLg
        border.width: 1
        border.color: s_.borderBright
    }

    header: Rectangle {
        height: 56; color: "transparent"
        RowLayout {
            anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.lg }
            Text {
                text:           root.contextNameValue.length > 0 ? "Edit Context" : "New Context"
                color:          s_.textPrimary
                font.pixelSize: s_.fontXl
                font.bold:      true
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                width: 28; height: 28; radius: 14
                color: xHov_.containsMouse ? s_.border : "transparent"
                Text { anchors.centerIn: parent; text: "✕"; color: s_.textSecondary; font.pixelSize: s_.fontMd }
                MouseArea { id: xHov_; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
            }
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: s_.border }
    }

    footer: Rectangle {
        height: 56; color: "transparent"
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: s_.border }
        RowLayout {
            anchors { fill: parent; leftMargin: s_.xl; rightMargin: s_.xl }
            Item { Layout.fillWidth: true }
            CardButton { label: "Cancel"; onClicked: root.close() }
            Item { width: s_.sm }
            CardButton { label: "Save"; accent: true; onClicked: root.close() }
        }
    }

    Style { id: s_ }

    contentItem: ColumnLayout {
        spacing: s_.lg

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
                height: 72; radius: s_.radiusSm
                color: s_.surface; border.width: 1; border.color: s_.border
                TextArea {
                    anchors.fill: parent
                    leftPadding: s_.md; rightPadding: s_.md
                    topPadding: s_.sm; bottomPadding: s_.sm
                    text:            root.descriptionValue.length > 0 ? root.descriptionValue : "A short description of this context."
                    color:           s_.textPrimary
                    font.pixelSize:  s_.fontMd
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
                spacing: s_.sm
                Repeater {
                    model: [
                        { label: "Shell",   val: "shell",   col: s_.colorShell   },
                        { label: "Maya",    val: "maya",    col: s_.colorMaya    },
                        { label: "Houdini", val: "houdini", col: s_.colorHoudini },
                        { label: "Custom",  val: "custom",  col: s_.colorCustom  }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        height: 32; width: selLbl_.implicitWidth + 24
                        radius: s_.radiusSm
                        property bool isSelected: root.launchTargetValue === modelData.val
                        color: isSelected
                            ? Qt.rgba(modelData.col.r, modelData.col.g, modelData.col.b, 0.15)
                            : (selHov_.containsMouse ? Qt.rgba(1,1,1,0.04) : "transparent")
                        border.width: 1
                        border.color: isSelected
                            ? Qt.rgba(modelData.col.r, modelData.col.g, modelData.col.b, 0.5)
                            : s_.border
                        Behavior on color { ColorAnimation { duration: 80 } }
                        Text {
                            id: selLbl_
                            anchors.centerIn: parent
                            text:           modelData.label
                            color:          isSelected ? modelData.col : s_.textSecondary
                            font.pixelSize: s_.fontMd
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
                    width: 64; height: 64; radius: s_.radiusSm
                    color: s_.surface; border.width: 1; border.color: s_.border
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
        Style { id: s_ }
        spacing: s_.xs
        Text {
            text:           parent.label
            color:          s_.textSecondary
            font.pixelSize: s_.fontSm
        }
        ColumnLayout { id: contentHolder_; spacing: 0 }
    }

    component FieldInput: Rectangle {
        property alias text:     ti_.text
        property bool  monospace: false
        Style { id: s_ }
        height: 36; radius: s_.radiusSm
        color: s_.surface; border.width: 1; border.color: s_.border
        TextInput {
            id: ti_
            anchors.left: parent.left; anchors.right: parent.right
            anchors.leftMargin: s_.md; anchors.rightMargin: s_.md
            anchors.verticalCenter: parent.verticalCenter
            color:           s_.textPrimary
            font.pixelSize:  s_.fontMd
            font.family:     monospace ? "Consolas, Courier New, monospace" : font.family
            selectByMouse:   true
        }
    }

    component FieldCombo: ComboBox {
        Style { id: s_ }
        height: 36
        background: Rectangle {
            color: s_.surface; radius: s_.radiusSm
            border.width: 1; border.color: s_.border
        }
        contentItem: Text {
            leftPadding: s_.md
            text:            parent.displayText
            color:           s_.textPrimary
            font.pixelSize:  s_.fontMd
            verticalAlignment: Text.AlignVCenter
        }
        popup: Popup {
            y: parent.height + 4
            width: parent.width
            background: Rectangle {
                color: s_.elevated; radius: s_.radiusSm
                border.width: 1; border.color: s_.borderBright
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
                color: parent.hovered ? s_.elevated : "transparent"
            }
            contentItem: Text {
                leftPadding:     s_.md
                text:            modelData
                color:           s_.textPrimary
                font.pixelSize:  s_.fontMd
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
