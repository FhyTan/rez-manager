pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Dialog {
    id: root
    title: "Confirm Delete"
    modal: true
    width: 460
    padding: Style.xl

    property string messageText: ""
    signal confirmed()

    standardButtons: Dialog.Yes | Dialog.Cancel
    onAccepted: {
        root.confirmed();
        root.close();
    }
    onRejected: root.close()

    contentItem: ColumnLayout {
        spacing: Style.md

        Text {
            Layout.fillWidth: true
            text: root.messageText
            color: Style.textPrimary
            font.pixelSize: Style.fontMd
            wrapMode: Text.WordWrap
        }
    }
}
