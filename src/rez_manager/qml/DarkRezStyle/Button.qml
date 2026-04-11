import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import ".."

T.Button {
    id: control

    readonly property bool accentButton: control.highlighted

    implicitWidth: Math.max(92, implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(36, implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)

    hoverEnabled: true
    spacing: Style.sm
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm
    bottomPadding: Style.sm

    contentItem: Text {
        text: control.text
        color: control.accentButton ? Style.white : control.enabled ? Style.textPrimary : Style.textDisabled
        font.pixelSize: Style.fontMd
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 92
        implicitHeight: 36
        radius: Style.radiusSm
        color: control.accentButton ? control.down ? Qt.darker(Style.accent, 1.16) : control.hovered ? Style.accentHover : Style.accent : control.down ? Style.controlPressed : control.hovered ? Style.controlHover : Style.card
        border.width: 1
        border.color: control.accentButton ? Style.borderAccent : control.visualFocus ? Style.accentHover : control.hovered ? Style.borderBright : Style.border

        Behavior on color {
            ColorAnimation {
                duration: 90
            }
        }

        Behavior on border.color {
            ColorAnimation {
                duration: 90
            }
        }
    }
}
