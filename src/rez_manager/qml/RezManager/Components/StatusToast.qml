pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property string messageText: ""
    property color accentColor: Style.success
    property bool shown: false

    signal activated

    function show(messageText, accentColor) {
        root.messageText = String(messageText ?? "");
        root.accentColor = accentColor ?? Style.success;
        root.shown = root.messageText.length > 0;
        if (!root.shown)
            return;
        if (hoverHandler_.hovered)
            hideTimer_.stop();
        else
            hideTimer_.restart();
    }

    anchors {
        bottom: parent.bottom
        horizontalCenter: parent.horizontalCenter
        bottomMargin: Style.xl
    }
    width: Math.min(parent ? parent.width - Style.xl * 2 : toastLayout_.implicitWidth + Style.xl * 2, toastLayout_.implicitWidth + Style.xl * 2)
    implicitHeight: toastLayout_.implicitHeight + Style.xl
    radius: Style.radius
    color: Style.elevated
    border.width: 1
    border.color: Style.borderBright
    visible: root.shown || opacity > 0.0
    opacity: root.shown ? 1.0 : 0.0

    Behavior on opacity {
        NumberAnimation {
            duration: 200
        }
    }

    Timer {
        id: hideTimer_
        interval: 3000
        onTriggered: root.shown = false
    }

    HoverHandler {
        id: hoverHandler_
        cursorShape: Qt.PointingHandCursor
        onHoveredChanged: {
            if (hovered)
                hideTimer_.stop();
            else if (root.shown)
                hideTimer_.restart();
        }
    }

    TapHandler {
        gesturePolicy: TapHandler.WithinBounds
        onTapped: root.activated()
    }

    RowLayout {
        id: toastLayout_
        anchors {
            fill: parent
            leftMargin: Style.md
            rightMargin: Style.md
            topMargin: Style.sm
            bottomMargin: Style.sm
        }
        spacing: Style.sm

        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: 8
            implicitHeight: 8
            radius: 4
            color: root.accentColor
        }

        Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            text: root.messageText
            color: Style.textPrimary
            font.pixelSize: Style.fontMd
            wrapMode: Text.Wrap
        }
    }
}
