import QtQuick
import QtQuick.Templates as T
import ".."

T.MenuSeparator {
    id: control

    implicitWidth: 160
    implicitHeight: Style.md + 1
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.xs
    bottomPadding: Style.xs

    contentItem: Rectangle {
        implicitWidth: 160
        implicitHeight: 1
        color: Style.border
        opacity: 0.9
    }
}
