import QtQuick
import QtQuick.Templates as T
import ".."

T.SpinBox {
    id: control

    readonly property color hoverBackgroundColor: Qt.lighter(Style.card, 1.08)
    readonly property color pressedAccentColor: Qt.darker(Style.accent, 1.16)

    implicitWidth: Math.max(140, implicitBackgroundWidth + leftInset + rightInset,
                            contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(38, implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding,
                             up.implicitIndicatorHeight, down.implicitIndicatorHeight)

    editable: true
    padding: Style.sm
    leftPadding: padding + (control.mirrored ? (up.indicator ? up.indicator.width : 0) : (down.indicator ? down.indicator.width : 0))
    rightPadding: padding + (control.mirrored ? (down.indicator ? down.indicator.width : 0) : (up.indicator ? up.indicator.width : 0))

    hoverEnabled: true

    validator: IntValidator {
        locale: control.locale.name
        bottom: Math.min(control.from, control.to)
        top: Math.max(control.from, control.to)
    }

    contentItem: TextInput {
        z: 2
        text: control.displayText
        clip: width < implicitWidth

        font.pixelSize: Style.fontMd
        color: Style.textPrimary
        selectionColor: Style.accent
        selectedTextColor: Style.white
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter

        readOnly: !control.editable
        validator: control.validator
        inputMethodHints: control.inputMethodHints
    }

    up.indicator: Rectangle {
        x: control.mirrored ? 0 : control.width - width
        height: control.height
        implicitWidth: 32
        implicitHeight: 40
        radius: Style.radiusSm
        color: control.up.pressed ? control.pressedAccentColor : Style.card
        border.width: 1
        border.color: Style.border

        Text {
            anchors.centerIn: parent
            text: "▲"
            color: control.up.pressed ? Style.white : Style.textSecondary
            font.pixelSize: Style.fontSm
        }
    }

    down.indicator: Rectangle {
        x: control.mirrored ? parent.width - width : 0
        height: control.height
        implicitWidth: 32
        implicitHeight: 40
        radius: Style.radiusSm
        color: control.down.pressed ? control.pressedAccentColor : Style.card
        border.width: 1
        border.color: Style.border

        Text {
            anchors.centerIn: parent
            text: "▼"
            color: control.down.pressed ? Style.white : Style.textSecondary
            font.pixelSize: Style.fontSm
        }
    }

    background: Rectangle {
        implicitWidth: 140
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
                target: control.background
                color: Style.card
                border.color: Style.border
            }
        },
        State {
            name: "focused"
            when: control.enabled && control.activeFocus

            PropertyChanges {
                target: control.contentItem
                color: Style.textPrimary
            }

            PropertyChanges {
                target: control.background
                color: Style.surface
                border.color: Style.accent
            }
        },
        State {
            name: "hover"
            when: control.enabled && control.hovered && !control.activeFocus

            PropertyChanges {
                target: control.contentItem
                color: Style.textPrimary
            }

            PropertyChanges {
                target: control.background
                color: control.hoverBackgroundColor
                border.color: Style.borderBright
            }
        }
    ]
    // qmllint enable
}
