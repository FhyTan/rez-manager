import QtQuick
import QtQuick.Templates as T
import ".."

T.MenuItem {
    id: control

    property color itemColor: Style.textPrimary
    property color hoverColor: Qt.tint(Style.elevated, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.16))
    property color pressedColor: Qt.tint(Style.elevated, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.24))

    implicitWidth: Math.max(160, implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(34, implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding)
    padding: 0
    leftPadding: Style.md
    rightPadding: Style.md
    topPadding: Style.sm
    bottomPadding: Style.sm

    background: Rectangle {
        id: background_
        implicitWidth: control.implicitWidth
        implicitHeight: control.implicitHeight
        radius: Style.radiusSm
        color: "transparent"

        Behavior on color {
            ColorAnimation {
                duration: 70
            }
        }
    }

    contentItem: Text {
        id: label_
        text: control.text
        color: control.itemColor
        font.family: control.font.family
        font.weight: control.font.weight
        font.pixelSize: Style.fontMd
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
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
            }
        },
        State {
            name: "pressed"
            when: control.enabled && control.down

            PropertyChanges {
                target: label_
                color: control.itemColor
            }

            PropertyChanges {
                target: background_
                color: control.pressedColor
            }
        },
        State {
            name: "highlighted"
            when: control.enabled && control.highlighted

            PropertyChanges {
                target: label_
                color: control.itemColor
            }

            PropertyChanges {
                target: background_
                color: control.hoverColor
            }
        }
    ]
    // qmllint enable
}
