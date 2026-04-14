import QtQuick 2.15
import QtQuick.Controls
import QtQuick.Layouts 1.15
import ".."

// Sidebar project list item.
// Usage: ProjectListItem { projectName: "VFX Pipeline"; avatarColor: "#5F83FF"; selected: true }
Rectangle {
    id: root
    property string projectName:  "Project"
    property color  avatarColor:  Style.accent
    property bool   selected:     false

    signal clicked
    signal editRequested
    signal duplicateRequested
    signal deleteRequested


    height: 44
    radius: Style.radiusSm
    color:  selected
        ? Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.10)
        : (hover_.hovered ? Qt.rgba(1,1,1,0.03) : "transparent")

    Behavior on color { ColorAnimation { duration: 100 } }

    // Selected left accent bar
    Rectangle {
        anchors.left:   parent.left
        anchors.top:    parent.top
        anchors.bottom: parent.bottom
        width:   3
        radius:  2
        color:   root.selected ? Style.accent : "transparent"
    }

    RowLayout {
        anchors {
            left: parent.left; leftMargin: 14
            right: parent.right; rightMargin: 12
            verticalCenter: parent.verticalCenter
        }
        spacing: 10

        // Avatar circle
        Rectangle {
            width: 30; height: 30; radius: 15
            color:        Qt.rgba(root.avatarColor.r, root.avatarColor.g, root.avatarColor.b, 0.18)
            border.width: 1
            border.color: Qt.rgba(root.avatarColor.r, root.avatarColor.g, root.avatarColor.b, 0.4)

            Text {
                anchors.centerIn: parent
                text:            root.projectName.length > 0 ? root.projectName[0].toUpperCase() : "?"
                color:           root.avatarColor
                font.pixelSize:  Style.fontSm
                font.bold:       true
            }
        }

        Text {
            Layout.fillWidth: true
            text:            root.projectName
            color:           root.selected ? Style.textPrimary : Style.textSecondary
            font.pixelSize:  Style.fontMd
            font.weight:     root.selected ? Font.Medium : Font.Normal
            elide:           Text.ElideRight
        }

    }

    HoverHandler {
        id: hover_
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onTapped: root.clicked()
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: function(eventPoint) {
            projectMenu_.popup(root, eventPoint.position.x, eventPoint.position.y)
        }
    }

    Menu {
        id: projectMenu_
        MenuItem {
            text: "Edit"
            onTriggered: root.editRequested()
        }
        MenuItem {
            text: "Duplicate"
            onTriggered: root.duplicateRequested()
        }
        MenuItem {
            text: "Delete"
            onTriggered: root.deleteRequested()
        }
    }
}
