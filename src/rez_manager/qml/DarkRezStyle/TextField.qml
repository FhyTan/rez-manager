import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import ".."

T.TextField {
    id: control

    readonly property color hoverBackgroundColor: Qt.lighter(Style.card, 1.08)

    implicitWidth: Math.max(160, implicitBackgroundWidth + leftInset + rightInset, Math.max(contentWidth, placeholder_.implicitWidth) + leftPadding + rightPadding)
    implicitHeight: Math.max(38, implicitBackgroundHeight + topInset + bottomInset, contentHeight + topPadding + bottomPadding, placeholder_.implicitHeight + topPadding + bottomPadding)

    hoverEnabled: true
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm + 1
    bottomPadding: Style.sm + 1
    color: Style.textPrimary
    selectionColor: Style.accent
    selectedTextColor: Style.white
    placeholderTextColor: Style.textDisabled
    verticalAlignment: TextInput.AlignVCenter

    background: Rectangle {
        id: background_
        implicitWidth: 160
        implicitHeight: 38
        radius: Style.radiusSm
        color: Style.card
        border.width: 1
        border.color: Style.border

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

    PlaceholderText {
        id: placeholder_
        x: control.leftPadding
        y: control.topPadding
        width: control.width - (control.leftPadding + control.rightPadding)
        height: control.height - (control.topPadding + control.bottomPadding)
        text: control.placeholderText
        font: control.font
        color: control.placeholderTextColor
        verticalAlignment: control.verticalAlignment
        visible: !control.length && !control.preeditText && (!control.activeFocus || control.horizontalAlignment !== Qt.AlignHCenter)
        elide: Text.ElideRight
        renderType: control.renderType
    }

    // qmllint disable
    states: [
        State {
            name: "disabled"
            when: !control.enabled

            PropertyChanges {
                target: control
                color: Style.textDisabled
            }

            PropertyChanges {
                target: background_
                color: Style.card
                border.color: Style.border
            }
        },
        State {
            name: "focused"
            when: control.enabled && control.activeFocus

            PropertyChanges {
                target: control
                color: Style.textPrimary
            }

            PropertyChanges {
                target: background_
                color: Style.surface
                border.color: Style.accent
            }
        },
        State {
            name: "hover"
            when: control.enabled && control.hovered

            PropertyChanges {
                target: control
                color: Style.textPrimary
            }

            PropertyChanges {
                target: background_
                color: control.hoverBackgroundColor
                border.color: Style.borderBright
            }
        }
    ]
    // qmllint enable

}
