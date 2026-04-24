import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import ".."

T.TextArea {
    id: control

    readonly property color hoverBackgroundColor: Qt.lighter(Style.card, 1.08)

    implicitWidth: Math.max(240, contentWidth + leftPadding + rightPadding, implicitBackgroundWidth + leftInset + rightInset, placeholder_.implicitWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(92, contentHeight + topPadding + bottomPadding, implicitBackgroundHeight + topInset + bottomInset, placeholder_.implicitHeight + topPadding + bottomPadding)

    hoverEnabled: true
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.md
    bottomPadding: Style.md
    color: Style.textPrimary
    selectionColor: Style.accent
    selectedTextColor: Style.white
    placeholderTextColor: Style.textDisabled

    background: Rectangle {
        id: background_
        implicitWidth: 240
        implicitHeight: 92
        radius: Style.radius
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
