import QtQuick
import QtQuick.Templates as T
import ".."

T.CheckBox {
    id: control

    readonly property color pressedAccentColor: Qt.darker(Style.accent, 1.16)

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding,
                             implicitIndicatorHeight + topPadding + bottomPadding)

    padding: Style.sm
    spacing: Style.sm
    hoverEnabled: true

    indicator: Rectangle {
        implicitWidth: 22
        implicitHeight: 22

        x: control.text ? (control.mirrored ? control.width - width - control.rightPadding : control.leftPadding) : control.leftPadding + (control.availableWidth - width) / 2
        y: control.topPadding + (control.availableHeight - height) / 2

        radius: Style.radiusSm
        color: Style.card
        border.width: 1
        border.color: Style.border

        Text {
            anchors.centerIn: parent
            text: "✓"
            color: Style.white
            font.pixelSize: Style.fontSm
            font.bold: true
            visible: control.checkState === Qt.Checked
        }

        Rectangle {
            anchors.centerIn: parent
            width: 12
            height: 3
            radius: 1.5
            color: Style.white
            visible: control.checkState === Qt.PartiallyChecked
        }
    }

    contentItem: Text {
        leftPadding: control.indicator && !control.mirrored ? control.indicator.width + control.spacing : 0
        rightPadding: control.indicator && control.mirrored ? control.indicator.width + control.spacing : 0

        text: control.text
        font.pixelSize: Style.fontMd
        color: Style.textPrimary
        verticalAlignment: Text.AlignVCenter
    }

    // qmllint disable
    states: [
        State {
            name: "disabled"
            when: !control.enabled

            PropertyChanges {
                target: control.contentItem
                color: Style.textDisabled
            }

            PropertyChanges {
                target: control.indicator
                color: Style.card
                border.color: Style.border
            }
        },
        State {
            name: "pressed"
            when: control.enabled && control.down

            PropertyChanges {
                target: control.indicator
                color: control.pressedAccentColor
                border.color: Style.accent
            }
        },
        State {
            name: "hover"
            when: control.enabled && control.hovered && !control.down

            PropertyChanges {
                target: control.indicator
                color: Style.cardHover
                border.color: Style.borderBright
            }
        },
        State {
            name: "focused"
            when: control.enabled && control.visualFocus

            PropertyChanges {
                target: control.indicator
                border.color: Style.accentHover
            }
        }
    ]
    // qmllint enable
}
