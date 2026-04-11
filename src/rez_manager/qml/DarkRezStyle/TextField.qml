import QtQuick
import QtQuick.Templates as T
import ".."

T.TextField {
    id: control

    implicitWidth: 160
    implicitHeight: 38

    hoverEnabled: true
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm + 1
    bottomPadding: Style.sm + 1
    color: control.enabled ? Style.textPrimary : Style.textDisabled
    selectionColor: Style.accent
    selectedTextColor: Style.white
    placeholderTextColor: Style.textDisabled

    background: Rectangle {
        implicitWidth: 160
        implicitHeight: 38
        radius: Style.radiusSm
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
