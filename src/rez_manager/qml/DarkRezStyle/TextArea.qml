import QtQuick
import QtQuick.Templates as T
import ".."

T.TextArea {
    id: control

    implicitWidth: 240
    implicitHeight: 92

    hoverEnabled: true
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.md
    bottomPadding: Style.md
    color: control.enabled ? Style.textPrimary : Style.textDisabled
    selectionColor: Style.accent
    selectedTextColor: Style.white
    placeholderTextColor: Style.textDisabled

    background: Rectangle {
        implicitWidth: 240
        implicitHeight: 92
        radius: Style.radius
        color: control.activeFocus ? Style.surface : Style.card
        border.width: 1
        border.color: control.activeFocus ? Style.accent : control.hovered ? Style.borderBright : Style.border

        Behavior on color {
            ColorAnimation {
                duration: 100
            }
        }

        Behavior on border.color {
            ColorAnimation {
                duration: 100
            }
        }
    }
}
