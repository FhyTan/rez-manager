import QtQuick
import QtQuick.Templates as T
import ".."

T.MenuBarItem {
    id: control

    readonly property color highlightColor: Qt.tint(Style.card, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.18))
    readonly property color pressedColor: Qt.tint(Style.card, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.28))

    implicitWidth: Math.max(68, implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(32, implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)

    padding: 0
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm
    bottomPadding: Style.sm

    contentItem: Text {
        id: label_
        text: control.text
        color: Style.textPrimary
        font.family: control.font.family
        font.weight: Font.Medium
        font.pixelSize: Style.fontMd
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        id: background_
        implicitWidth: control.implicitWidth
        implicitHeight: control.implicitHeight
        radius: Style.radiusSm
        color: "transparent"
        border.width: control.highlighted ? 1 : 0
        border.color: Style.borderBright

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
                color: "transparent"
                border.color: "transparent"
            }
        },
        State {
            name: "pressed"
            when: control.enabled && control.down

            PropertyChanges {
                target: background_
                color: control.pressedColor
                border.color: Style.borderBright
            }
        },
        State {
            name: "highlighted"
            when: control.enabled && control.highlighted

            PropertyChanges {
                target: background_
                color: control.highlightColor
                border.color: Style.borderBright
            }
        },
        State {
            name: "hovered"
            when: control.enabled && control.hovered

            PropertyChanges {
                target: background_
                color: control.highlightColor
                border.color: "transparent"
            }
        }
    ]
    // qmllint enable
}
