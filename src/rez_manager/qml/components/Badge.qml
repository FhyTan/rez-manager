import QtQuick 2.15
import ".."

// Small colored pill badge.
// Usage: Badge { text: "Maya"; badgeColor: s.colorMaya }
Rectangle {
    id: root
    property string text: ""
    property color  badgeColor: s_.accent

    Style { id: s_ }

    height: 20
    width:  Math.max(badgeLabel.implicitWidth + 14, 36)
    radius: height / 2
    color:  Qt.rgba(badgeColor.r, badgeColor.g, badgeColor.b, 0.15)
    border.width: 1
    border.color: Qt.rgba(badgeColor.r, badgeColor.g, badgeColor.b, 0.45)

    Text {
        id: badgeLabel
        anchors.centerIn: parent
        text:  root.text
        color: root.badgeColor
        font.pixelSize: s_.fontXs
        font.bold: true
    }
}
