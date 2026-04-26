import QtQuick
import QtQuick.Templates as T
import ".."

T.Button {
    id: control

    readonly property bool accentButton: control.highlighted
    readonly property color accentPressedColor: Qt.darker(Style.accent, 1.16)
    readonly property color accentBorderColor: Qt.tint(Style.border, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.55))
    readonly property color neutralHoverColor: Qt.lighter(Style.card, 1.08)
    readonly property color neutralPressedColor: Qt.lighter(Style.card, 1.14)

    implicitWidth: Math.max(92, implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(36, implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)

    hoverEnabled: true
    spacing: Style.sm
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm
    bottomPadding: Style.sm

    contentItem: Text {
        id: label_
        text: control.text
        color: Style.textPrimary
        font.pixelSize: Style.fontMd
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        id: background_
        implicitWidth: 92
        implicitHeight: 36
        radius: Style.radiusSm
        color: Style.card
        border.width: 1
        border.color: Style.border

        Behavior on color {
            ColorAnimation {
                duration: 90
            }
        }

        Behavior on border.color {
            ColorAnimation {
                duration: 90
            }
        }
    }

    // qmllint disable
    states: [
        State {
            name: "disabled"
            when: !control.enabled

            PropertyChanges {
                target: label_
                color: Style.textDisabled
            }

            PropertyChanges {
                target: background_
                color: Style.card
                border.color: Style.border
            }
        },
        State {
            name: "accentPressed"
            when: control.enabled && control.accentButton && control.down

            PropertyChanges {
                target: label_
                color: Style.white
            }

            PropertyChanges {
                target: background_
                color: control.accentPressedColor
                border.color: control.accentBorderColor
            }
        },
        State {
            name: "accentHover"
            when: control.enabled && control.accentButton && control.hovered

            PropertyChanges {
                target: label_
                color: Style.white
            }

            PropertyChanges {
                target: background_
                color: Style.accentHover
                border.color: control.accentBorderColor
            }
        },
        State {
            name: "accent"
            when: control.enabled && control.accentButton

            PropertyChanges {
                target: label_
                color: Style.white
            }

            PropertyChanges {
                target: background_
                color: Style.accent
                border.color: control.accentBorderColor
            }
        },
        State {
            name: "pressed"
            when: control.enabled && control.down

            PropertyChanges {
                target: label_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: background_
                color: control.neutralPressedColor
                border.color: Style.borderBright
            }
        },
        State {
            name: "hover"
            when: control.enabled && control.hovered

            PropertyChanges {
                target: label_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: background_
                color: control.neutralHoverColor
                border.color: Style.borderBright
            }
        }
    ]
    // qmllint enable
}
