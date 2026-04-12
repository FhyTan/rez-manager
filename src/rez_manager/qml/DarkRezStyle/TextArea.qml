import QtQuick
import QtQuick.Templates as T
import ".."

T.TextArea {
    id: control

    readonly property color hoverBackgroundColor: Qt.lighter(Style.card, 1.08)

    implicitWidth: 240
    implicitHeight: 92

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
}
