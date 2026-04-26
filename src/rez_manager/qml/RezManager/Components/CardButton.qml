import QtQuick 2.15
import ".."

// Reusable action button for cards and toolbars.
// Usage: CardButton { glyph: "▶"; label: "Launch"; accent: true; onClicked: ... }
Rectangle {
    id: root
    property string label: ""
    property string glyph: ""
    property bool accent: false
    property bool danger: false
    property bool square: false
    property int minimumWidth: 80

    signal clicked

    property string text: {
        if (glyph.length > 0 && label.length > 0)
            return glyph + "  " + label;
        if (glyph.length > 0)
            return glyph;
        return label;
    }

    implicitHeight: 30
    implicitWidth: root.square ? implicitHeight : Math.max(root.minimumWidth, label_.implicitWidth + 20)
    radius: Style.radiusSm
    color: {
        if (root.danger)
            return tapHandler_.pressed ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.20) : hoverHandler_.hovered ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.14) : Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.10);
        if (root.accent)
            return tapHandler_.pressed ? Qt.darker(Style.accent, 1.12) : hoverHandler_.hovered ? Style.accentHover : Style.accent;
        return hoverHandler_.hovered ? Qt.rgba(1, 1, 1, 0.04) : "transparent";
    }
    border.width: root.accent || root.danger || hoverHandler_.hovered ? 1 : 0
    border.color: root.danger ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.35) : hoverHandler_.hovered ? Style.borderBright : Style.border

    Behavior on color {
        ColorAnimation {
            duration: 100
        }
    }

    Text {
        id: label_
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        text: root.text
        color: root.accent ? Style.white : root.danger ? Style.error : Style.textPrimary
        font.pixelSize: Style.fontSm
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    HoverHandler {
        id: hoverHandler_
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    TapHandler {
        id: tapHandler_
        gesturePolicy: TapHandler.WithinBounds
        enabled: root.enabled
        acceptedButtons: Qt.LeftButton
        onTapped: root.clicked()
    }
}
