pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import ".."

T.ComboBox {
    id: control

    readonly property color delegateHoverColor: Qt.tint(Style.elevated, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.22))
    readonly property color delegatePressedColor: Qt.tint(Style.elevated, Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.30))
    readonly property color hoverBackgroundColor: Qt.lighter(Style.card, 1.08)

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

        width: ListView.view ? ListView.view.width : control.width
        height: 36
        hoverEnabled: true
        leftPadding: Style.md
        rightPadding: Style.md
        topPadding: Style.sm
        bottomPadding: Style.sm

        contentItem: Text {
            id: delegateLabel_
            text: comboDelegate_.textValue
            color: Style.textPrimary
            font.pixelSize: Style.fontMd
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Rectangle {
            id: delegateBackground_
            radius: Style.radiusSm
            color: control.delegateHoverColor
            opacity: 0.0

            Behavior on opacity {
                NumberAnimation {
                    duration: 70
                }
            }
        }

        states: [
            State {
                name: "pressed"
                when: comboDelegate_.down

                PropertyChanges {
                    target: delegateLabel_
                    color: Style.white
                }

                PropertyChanges {
                    target: delegateBackground_
                    color: control.delegatePressedColor
                    opacity: 1.0
                }
            },
            State {
                name: "hover"
                when: comboDelegate_.hovered || comboDelegate_.highlighted

                PropertyChanges {
                    target: delegateLabel_
                    color: Style.white
                }

                PropertyChanges {
                    target: delegateBackground_
                    color: control.delegateHoverColor
                    opacity: 1.0
                }
            }
        ]

        onClicked: {
            control.currentIndex = index;
            control.activated(index);
            control.popup.close();
        }
    }

    indicator: Text {
        id: indicator_
        x: control.width - width - Style.md
        y: (control.height - height) / 2
        text: "▾"
        color: Style.textSecondary
        font.pixelSize: Style.fontLg
    }

    contentItem: Text {
        id: displayText_
        leftPadding: 0
        rightPadding: 0
        text: control.displayText
        font.pixelSize: Style.fontMd
        color: Style.textPrimary
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        id: background_
        implicitWidth: 148
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

    states: [
        State {
            name: "disabled"
            when: !control.enabled

            PropertyChanges {
                target: displayText_
                color: Style.textDisabled
            }

            PropertyChanges {
                target: indicator_
                color: Style.textDisabled
            }

            PropertyChanges {
                target: background_
                color: Style.card
                border.color: Style.border
            }
        },
        State {
            name: "popupOpen"
            when: control.popup.visible

            PropertyChanges {
                target: displayText_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: indicator_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: background_
                color: Style.elevated
                border.color: Style.accentHover
            }
        },
        State {
            name: "pressed"
            when: control.enabled && control.down

            PropertyChanges {
                target: displayText_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: indicator_
                color: Style.textSecondary
            }

            PropertyChanges {
                target: background_
                color: Style.elevated
                border.color: Style.borderBright
            }
        },
        State {
            name: "focus"
            when: control.enabled && control.visualFocus

            PropertyChanges {
                target: displayText_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: indicator_
                color: Style.textSecondary
            }

            PropertyChanges {
                target: background_
                color: Style.card
                border.color: Style.accentHover
            }
        },
        State {
            name: "hover"
            when: control.enabled && control.hovered

            PropertyChanges {
                target: displayText_
                color: Style.textPrimary
            }

            PropertyChanges {
                target: indicator_
                color: Style.textSecondary
            }

            PropertyChanges {
                target: background_
                color: control.hoverBackgroundColor
                border.color: Style.borderBright
            }
        }
    ]

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
