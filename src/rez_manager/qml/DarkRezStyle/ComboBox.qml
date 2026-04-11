pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import ".."

T.ComboBox {
    id: control

    implicitWidth: Math.max(148, implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(38, implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)

    spacing: Style.sm
    leftPadding: Style.md
    rightPadding: Style.xxl + Style.xs
    topPadding: Style.sm
    bottomPadding: Style.sm
    hoverEnabled: true

    delegate: ItemDelegate {
        id: comboDelegate_
        required property int index
        required property var modelData
        readonly property string textValue: control.textRole.length > 0 && typeof comboDelegate_.modelData === "object" ? comboDelegate_.modelData[control.textRole] : comboDelegate_.modelData
        readonly property color fillColor: comboDelegate_.down ? Style.accentFillPressed : Style.accentFillHover

        width: ListView.view ? ListView.view.width : control.width
        height: 36
        hoverEnabled: true
        leftPadding: Style.md
        rightPadding: Style.md
        topPadding: Style.sm
        bottomPadding: Style.sm

        contentItem: Text {
            text: comboDelegate_.textValue
            color: comboDelegate_.down || comboDelegate_.hovered || comboDelegate_.highlighted ? Style.white : Style.textPrimary
            font.pixelSize: Style.fontMd
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Rectangle {
            radius: Style.radiusSm
            color: comboDelegate_.fillColor
            opacity: comboDelegate_.down || comboDelegate_.hovered || comboDelegate_.highlighted ? 1.0 : 0.0

            Behavior on opacity {
                NumberAnimation {
                    duration: 70
                }
            }
        }

        onClicked: {
            control.currentIndex = index;
            control.activated(index);
            control.popup.close();
        }
    }

    indicator: Text {
        x: control.width - width - Style.md
        y: (control.height - height) / 2
        text: "▾"
        color: control.popup.visible ? Style.textPrimary : control.enabled ? Style.textSecondary : Style.textDisabled
        font.pixelSize: Style.fontLg
    }

    contentItem: Text {
        leftPadding: 0
        rightPadding: 0
        text: control.displayText
        font.pixelSize: Style.fontMd
        color: control.enabled ? Style.textPrimary : Style.textDisabled
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 148
        implicitHeight: 38
        radius: Style.radiusSm
        color: control.down || control.popup.visible ? Style.elevated : control.hovered ? Style.controlHover : Style.card
        border.width: 1
        border.color: control.visualFocus || control.popup.visible ? Style.accentHover : control.hovered ? Style.borderBright : Style.border

        Behavior on color {
            ColorAnimation {
                duration: 100
            }
        }

        Behavior on border.color {
            ColorAnimation {
                duration: 100
            }
        }
    }

    popup: Popup {
        y: control.height + Style.xs
        width: control.width
        padding: Style.xs
        topPadding: Style.xs
        bottomPadding: Style.xs
        leftPadding: Style.xs
        rightPadding: Style.xs
        margins: Style.xs
        implicitHeight: Math.min(contentItem.implicitHeight + topPadding + bottomPadding, 236)

        background: Rectangle {
            radius: Style.radius
            color: Style.elevated
            border.width: 1
            border.color: Style.borderBright
        }

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            spacing: 2
            boundsBehavior: Flickable.StopAtBounds

            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }
}
