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


    implicitHeight: 30
    implicitWidth:  row_.implicitWidth + 18
    radius: Style.radiusSm

    color: {
        var base = accent ? Style.accent
                 : danger ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.12)
                 : "transparent"
        if (ma_.pressed)       return accent ? Qt.darker(base, 1.15) : Qt.rgba(1,1,1,0.04)
        if (ma_.containsMouse) return accent ? Style.accentHover : Qt.rgba(1,1,1,0.06)
        return base
    }
    border.width: accent ? 0 : 1
    border.color: danger
        ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.35)
        : (ma_.containsMouse ? Style.borderBright : Style.border)

    Behavior on color { ColorAnimation { duration: 80 } }

    Row {
        id: row_
        anchors.centerIn: parent
        spacing: 4

        Text {
            visible: root.icon.length > 0
            text:  root.icon
            color: accent ? Style.white
                 : danger  ? Style.error
                 : ma_.containsMouse ? Style.textPrimary : Style.textSecondary
            font.pixelSize: Style.fontSm
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text:  root.label
            color: accent ? Style.white
                 : danger  ? Style.error
                 : ma_.containsMouse ? Style.textPrimary : Style.textSecondary
            font.pixelSize: Style.fontSm
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
