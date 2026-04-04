import QtQuick 2.15
import ".."

// Reusable action button for cards and toolbars.
// Usage: CardButton { icon: "▶"; label: "Launch"; accent: true; onClicked: ... }
Rectangle {
    id: root
    property string label:  ""
    property string icon:   ""
    property bool   accent: false
    property bool   danger: false

    signal clicked

    Style { id: s_ }

    implicitHeight: 30
    implicitWidth:  row_.implicitWidth + 18
    radius: s_.radiusSm

    color: {
        var base = accent ? s_.accent
                 : danger ? Qt.rgba(s_.error.r, s_.error.g, s_.error.b, 0.12)
                 : "transparent"
        if (ma_.pressed)       return accent ? Qt.darker(base, 1.15) : Qt.rgba(1,1,1,0.04)
        if (ma_.containsMouse) return accent ? s_.accentHover : Qt.rgba(1,1,1,0.06)
        return base
    }
    border.width: accent ? 0 : 1
    border.color: danger
        ? Qt.rgba(s_.error.r, s_.error.g, s_.error.b, 0.35)
        : (ma_.containsMouse ? s_.borderBright : s_.border)

    Behavior on color { ColorAnimation { duration: 80 } }

    Row {
        id: row_
        anchors.centerIn: parent
        spacing: 4

        Text {
            visible: root.icon.length > 0
            text:  root.icon
            color: accent ? "#FFFFFF"
                 : danger  ? s_.error
                 : ma_.containsMouse ? s_.textPrimary : s_.textSecondary
            font.pixelSize: s_.fontSm
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text:  root.label
            color: accent ? "#FFFFFF"
                 : danger  ? s_.error
                 : ma_.containsMouse ? s_.textPrimary : s_.textSecondary
            font.pixelSize: s_.fontSm
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    MouseArea {
        id: ma_
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
