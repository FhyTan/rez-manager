import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: root

    property string tip: ""

    display: AbstractButton.IconOnly
    flat: true

    implicitWidth: 14
    implicitHeight: 14
    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0

    icon.source: "qrc:/icons/app/question.svg"
    icon.color: Style.textSecondary
    icon.width: 14
    icon.height: 14

    background: Item {}

    ToolTip {
        visible: root.hovered
        text: root.tip
        delay: 500
    }

    HoverHandler {
        cursorShape: Qt.WhatsThisCursor
    }
}
