import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import ".."

T.Dialog {
    id: control

    readonly property var footerButtons: [
        {
            visible: Boolean(control.standardButtons & Dialog.Cancel),
            text: qsTr("Cancel"),
            highlighted: false,
            action: function () {
                control.reject();
            }
        },
        {
            visible: Boolean(control.standardButtons & Dialog.Close),
            text: qsTr("Close"),
            highlighted: false,
            action: function () {
                control.reject();
            }
        },
        {
            visible: Boolean(control.standardButtons & Dialog.No),
            text: qsTr("No"),
            highlighted: false,
            action: function () {
                control.reject();
            }
        },
        {
            visible: Boolean(control.standardButtons & Dialog.Yes),
            text: qsTr("Yes"),
            highlighted: true,
            action: function () {
                control.accept();
            }
        },
        {
            visible: Boolean(control.standardButtons & Dialog.Ok),
            text: qsTr("OK"),
            highlighted: true,
            action: function () {
                control.accept();
            }
        },
        {
            visible: Boolean(control.standardButtons & Dialog.Save),
            text: qsTr("Save"),
            highlighted: true,
            action: function () {
                control.accept();
            }
        }
    ]

    implicitWidth: Math.max(420, implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding, implicitHeaderWidth, implicitFooterWidth)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset, implicitContentHeight + topPadding + bottomPadding + (implicitHeaderHeight > 0 ? implicitHeaderHeight + spacing : 0) + (implicitFooterHeight > 0 ? implicitFooterHeight + spacing : 0))

    spacing: 0
    leftPadding: Style.xl
    rightPadding: Style.xl
    topPadding: Style.xl
    bottomPadding: Style.xl
    closePolicy: Popup.CloseOnEscape

    T.Overlay.modal: Rectangle {
        color: Qt.rgba(0, 0, 0, 0.52)
    }

    T.Overlay.modeless: Rectangle {
        color: Qt.rgba(0, 0, 0, 0.32)
    }

    background: Rectangle {
        radius: Style.radiusLg
        color: Style.surface
        border.width: 1
        border.color: Style.borderBright
    }

    header: Rectangle {
        visible: control.title.length > 0
        implicitHeight: visible ? 56 : 0
        color: "transparent"

        Text {
            anchors {
                left: parent.left
                right: parent.right
                verticalCenter: parent.verticalCenter
                leftMargin: Style.xl
                rightMargin: Style.xl
            }
            text: control.title
            color: Style.textPrimary
            font.pixelSize: Style.fontLg
            font.bold: true
            elide: Text.ElideRight
        }

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: Style.border
        }
    }

    footer: Rectangle {
        visible: control.standardButtons !== 0
        implicitHeight: visible ? footerRow_.implicitHeight + Style.lg * 2 + 1 : 0
        color: "transparent"

        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: Style.border
        }

        Row {
            id: footerRow_
            anchors {
                fill: parent
                leftMargin: Style.lg
                rightMargin: Style.lg
                topMargin: Style.lg + 1
                bottomMargin: Style.lg
            }
            spacing: Style.sm
            layoutDirection: Qt.RightToLeft

            Repeater {
                model: control.footerButtons

                delegate: Button {
                    required property var modelData
                    visible: modelData.visible
                    text: modelData.text
                    highlighted: modelData.highlighted
                    onClicked: modelData.action()
                }
            }
        }
    }
}
