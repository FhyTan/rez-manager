import QtQuick
import QtQuick.Templates as T
import ".."

T.MenuSeparator {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm
    bottomPadding: Style.sm

    contentItem: Rectangle {
        implicitWidth: 188
        implicitHeight: 1
        radius: 0.5
        color: Style.borderBright
        opacity: 0.8
    }
}
