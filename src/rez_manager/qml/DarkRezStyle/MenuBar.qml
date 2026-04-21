import QtQuick
import QtQuick.Templates as T
import ".."

T.MenuBar {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(42, implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)

    spacing: Style.xs
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.xs
    bottomPadding: Style.xs

    delegate: MenuBarItem {}

    contentItem: Row {
        spacing: control.spacing

        Repeater {
            model: control.contentModel
        }
    }

    background: Rectangle {
        implicitHeight: 42
        color: Style.sidebar

        Rectangle {
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: 1
            color: Style.border
        }
    }
}
