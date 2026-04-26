pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Dialog {
    id: root
    title: "Duplicate Context"
    modal: true
    width: 460
    padding: Style.xl

    property string projectValue: ""
    property string contextNameValue: ""
    property var projectOptions: []
    signal submitted(string projectName, string contextName)

    function comboProjectOptions() {
        if (root.projectValue.length === 0)
            return root.projectOptions;
        if (root.projectOptions.indexOf(root.projectValue) >= 0)
            return root.projectOptions;
        return [root.projectValue].concat(root.projectOptions);
    }

    standardButtons: Dialog.Save | Dialog.Cancel
    onAboutToShow: {
        const projectIndex = projectCombo_.model.indexOf(root.projectValue);
        projectCombo_.currentIndex = projectIndex >= 0 ? projectIndex : 0;
        contextNameField_.text = root.contextNameValue;
    }
    onAccepted: {
        root.submitted(projectCombo_.currentText, contextNameField_.text);
    }
    onRejected: root.close()

    contentItem: ColumnLayout {
        spacing: Style.lg

        Text {
            text: "Project"
            color: Style.textSecondary
            font.pixelSize: Style.fontSm
        }

        ComboBox {
            id: projectCombo_
            Layout.fillWidth: true
            implicitHeight: 36
            model: root.comboProjectOptions()
        }

        Text {
            text: "Context name"
            color: Style.textSecondary
            font.pixelSize: Style.fontSm
        }

        TextField {
            id: contextNameField_
            Layout.fillWidth: true
            implicitHeight: 36
            selectByMouse: true
        }
    }
}
