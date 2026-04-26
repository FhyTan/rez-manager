pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Dialog {
    id: root
    title: "Project"
    modal: true
    width: 420
    padding: Style.xl

    property string projectNameValue: ""
    signal submitted(string projectName)

    standardButtons: Dialog.Save | Dialog.Cancel
    onAboutToShow: projectNameField_.text = root.projectNameValue
    onAccepted: {
        root.submitted(projectNameField_.text);
    }
    onRejected: root.close()

    contentItem: ColumnLayout {
        spacing: Style.lg

        Text {
            text: "Project name"
            color: Style.textSecondary
            font.pixelSize: Style.fontSm
        }

        TextField {
            id: projectNameField_
            Layout.fillWidth: true
            implicitHeight: 36
            selectByMouse: true
        }
    }
}
