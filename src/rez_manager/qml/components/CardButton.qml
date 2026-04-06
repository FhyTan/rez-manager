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
        var base = root.accent ? Style.accent
                 : root.danger ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.12)
                  : "transparent"
        if (tap_.pressed)       return root.accent ? Qt.darker(base, 1.15) : Qt.rgba(1,1,1,0.04)
        if (hover_.hovered)     return root.accent ? Style.accentHover : Qt.rgba(1,1,1,0.06)
        return base
    }
    border.width: root.accent ? 0 : 1
    border.color: root.danger
        ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.35)
        : (hover_.hovered ? Style.borderBright : Style.border)

    Behavior on color { ColorAnimation { duration: 80 } }

    Row {
        id: row_
        anchors.centerIn: parent
        spacing: 4

        Text {
            visible: root.icon.length > 0
            text:  root.icon
            color: root.accent ? Style.white
                 : root.danger ? Style.error
                 : hover_.hovered ? Style.textPrimary : Style.textSecondary
            font.pixelSize: Style.fontSm
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text:  root.label
            color: root.accent ? Style.white
                 : root.danger ? Style.error
                 : hover_.hovered ? Style.textPrimary : Style.textSecondary
            font.pixelSize: Style.fontSm
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    HoverHandler {
        id: hover_
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        id: tap_
        acceptedButtons: Qt.LeftButton
        onTapped: root.clicked()
    }
}
