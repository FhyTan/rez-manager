import QtQuick 2.15
import QtQuick.Layouts 1.15
import ".."

// Sidebar project list item.
// Usage: ProjectListItem { projectName: "VFX Pipeline"; avatarColor: "#5F83FF"; selected: true }
Rectangle {
    id: root
    property string projectName:  "Project"
    property color  avatarColor:  s_.accent
    property int    contextCount: 0
    property bool   selected:     false

    signal clicked

    Style { id: s_ }

    height: 44
    radius: s_.radiusSm
    color:  selected
        ? Qt.rgba(s_.accent.r, s_.accent.g, s_.accent.b, 0.10)
        : (ma_.containsMouse ? Qt.rgba(1,1,1,0.03) : "transparent")

    Behavior on color { ColorAnimation { duration: 100 } }

    // Selected left accent bar
    Rectangle {
        anchors.left:   parent.left
        anchors.top:    parent.top
        anchors.bottom: parent.bottom
        width:   3
        radius:  2
        color:   root.selected ? s_.accent : "transparent"
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
                font.pixelSize:  s_.fontSm
                font.bold:       true
            }
        }

        Text {
            Layout.fillWidth: true
            text:            root.projectName
            color:           root.selected ? s_.textPrimary : s_.textSecondary
            font.pixelSize:  s_.fontMd
            font.weight:     root.selected ? Font.Medium : Font.Normal
            elide:           Text.ElideRight
        }

        // Context count badge
        Rectangle {
            visible: root.contextCount > 0
            width:   countText_.implicitWidth + 10
            height:  18
            radius:  9
            color:   root.selected
                ? Qt.rgba(s_.accent.r, s_.accent.g, s_.accent.b, 0.25)
                : Qt.rgba(1,1,1,0.06)

            Text {
                id: countText_
                anchors.centerIn: parent
                text:            root.contextCount
                color:           root.selected ? s_.accent : s_.textDisabled
                font.pixelSize:  s_.fontXs
                font.bold:       true
            }
        }
    }

    MouseArea {
        id: ma_
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
