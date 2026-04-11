import QtQuick
import QtQuick.Templates as T
import ".."

T.MenuItem {
    id: control

    property color itemColor: Style.textPrimary
    property color hoverColor: Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.14)
    property color pressedColor: Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.20)

    implicitWidth: Math.max(
        160,
        implicitBackgroundWidth + leftInset + rightInset,
        implicitContentWidth + leftPadding + rightPadding
    )
    implicitHeight: Math.max(
        34,
        implicitBackgroundHeight + topInset + bottomInset,
        implicitContentHeight + topPadding + bottomPadding
    )
    padding: 0
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm
    bottomPadding: Style.sm

    background: Rectangle {
        implicitWidth: control.implicitWidth
        implicitHeight: control.implicitHeight
        radius: Style.radiusSm
        color: control.down ? control.pressedColor : control.highlighted ? control.hoverColor : "transparent"
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? control.itemColor : Style.textDisabled
        font.family: control.font.family
        font.weight: control.font.weight
        font.pixelSize: Style.fontMd
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}