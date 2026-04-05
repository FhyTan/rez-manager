import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

// Context card — the primary display unit for a Rez context.
// Signals: editInfoRequested, editPackagesRequested, previewRequested,
//          launchRequested, duplicateRequested, deleteRequested (right-click menu)
Rectangle {
    id: root

    // ── Public API ────────────────────────────────────────────
    property string contextName:  "Context Name"
    property string projectName:  "Project"
    property string description:  "No description."
    property string launchTarget: "shell"   // maya | houdini | shell | custom
    property string packages:     ""        // comma-separated list

    signal editInfoRequested
    signal editPackagesRequested
    signal previewRequested
    signal launchRequested
    signal duplicateRequested
    signal deleteRequested

    // ── Internal ─────────────────────────────────────────────

    property string initials: {
        var words = contextName.trim().split(/\s+/)
        if (words.length === 0)  return "??"
        if (words.length === 1)  return words[0].slice(0, 2).toUpperCase()
        return (words[0][0] + words[1][0]).toUpperCase()
    }

    property var packageList: {
        var raw = packages.split(",").map(function(p) { return p.trim() })
        return raw.filter(function(p) { return p.length > 0 })
    }

    property color accentColor: Style.launchColor(launchTarget)

    // ── Geometry ─────────────────────────────────────────────
    width:  365
    height: col_.implicitHeight + 3   // +3 for top accent strip
    radius: Style.radius

    color: hoverHandler_.hovered ? Style.cardHover : Style.card
    Behavior on color { ColorAnimation { duration: 100 } }

    // ── Border ────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        radius:       parent.radius
        color:        "transparent"
        border.width: 1
        border.color: hoverHandler_.hovered ? Style.borderBright : Style.border
    }

    // ── Top accent strip ─────────────────────────────────────
    Rectangle {
        id: strip_
        anchors.top:   parent.top
        anchors.left:  parent.left
        anchors.right: parent.right
        height: 3
        radius: Style.radius
        color:  root.accentColor
        // Flatten the bottom two corners of the strip
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left:   parent.left
            anchors.right:  parent.right
            height: Style.radius
            color:  parent.color
        }
    }

    // ── Hover & right-click capture ───────────────────────────
    // Pointer handlers don't block the child CardButton hover/click behavior.
    HoverHandler {
        id: hoverHandler_
    }
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: function(eventPoint, button) {
            contextMenu_.popup(root, eventPoint.position.x, eventPoint.position.y)
        }
    }

    // Right-click context menu
    Menu {
        id: contextMenu_
        topPadding: Style.xs
        bottomPadding: Style.xs

        background: Rectangle {
            implicitWidth: 184
            implicitHeight: 40
            color: Style.elevated
            radius: Style.radiusSm
            border.width: 1
            border.color: Style.borderBright
        }

        MenuItem {
            id: infoItem_
            implicitWidth: 184
            implicitHeight: 34
            text: "Edit Info…"
            background: Rectangle {
                implicitWidth: infoItem_.implicitWidth
                implicitHeight: infoItem_.implicitHeight
                color: infoItem_.highlighted ? Style.border : "transparent"
            }
            contentItem: Text {
                leftPadding: Style.md
                rightPadding: Style.md
                text: infoItem_.text
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
                verticalAlignment: Text.AlignVCenter
            }
            onTriggered: root.editInfoRequested()
        }
        MenuItem {
            id: packagesItem_
            implicitWidth: 184
            implicitHeight: 34
            text: "Edit Packages…"
            background: Rectangle {
                implicitWidth: packagesItem_.implicitWidth
                implicitHeight: packagesItem_.implicitHeight
                color: packagesItem_.highlighted ? Style.border : "transparent"
            }
            contentItem: Text {
                leftPadding: Style.md
                rightPadding: Style.md
                text: packagesItem_.text
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
                verticalAlignment: Text.AlignVCenter
            }
            onTriggered: root.editPackagesRequested()
        }
        MenuItem {
            id: previewItem_
            implicitWidth: 184
            implicitHeight: 34
            text: "Preview…"
            background: Rectangle {
                implicitWidth: previewItem_.implicitWidth
                implicitHeight: previewItem_.implicitHeight
                color: previewItem_.highlighted ? Style.border : "transparent"
            }
            contentItem: Text {
                leftPadding: Style.md
                rightPadding: Style.md
                text: previewItem_.text
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
                verticalAlignment: Text.AlignVCenter
            }
            onTriggered: root.previewRequested()
        }
        MenuSeparator {
            contentItem: Rectangle {
                implicitWidth: 184
                implicitHeight: 1
                color: Style.border
            }
        }
        MenuItem {
            id: duplicateItem_
            implicitWidth: 184
            implicitHeight: 34
            text: "Duplicate"
            background: Rectangle {
                implicitWidth: duplicateItem_.implicitWidth
                implicitHeight: duplicateItem_.implicitHeight
                color: duplicateItem_.highlighted ? Style.border : "transparent"
            }
            contentItem: Text {
                leftPadding: Style.md
                rightPadding: Style.md
                text: duplicateItem_.text
                color: Style.textPrimary
                font.pixelSize: Style.fontMd
                verticalAlignment: Text.AlignVCenter
            }
            onTriggered: root.duplicateRequested()
        }
        MenuItem {
            id: deleteItem_
            implicitWidth: 184
            implicitHeight: 34
            text: "Delete"
            background: Rectangle {
                implicitWidth: deleteItem_.implicitWidth
                implicitHeight: deleteItem_.implicitHeight
                color: deleteItem_.highlighted
                    ? Qt.rgba(Style.error.r, Style.error.g, Style.error.b, 0.15)
                    : "transparent"
            }
            contentItem: Text {
                leftPadding: Style.md
                rightPadding: Style.md
                text: deleteItem_.text
                color: Style.error
                font.pixelSize: Style.fontMd
                verticalAlignment: Text.AlignVCenter
            }
            onTriggered: root.deleteRequested()
        }
    }

    // ── Content ───────────────────────────────────────────────
    ColumnLayout {
        id: col_
        anchors {
            top:   strip_.bottom
            left:  parent.left
            right: parent.right
        }
        spacing: 0

        // Header: avatar + info + launch badge
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin:    Style.lg
            Layout.leftMargin:   Style.lg
            Layout.rightMargin:  Style.lg
            Layout.bottomMargin: Style.md
            spacing: Style.md

            // Avatar
            Rectangle {
                width:        58
                height:       58
                radius:       Style.radiusSm
                color:        Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.12)
                border.width: 1
                border.color: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.35)

                Text {
                    anchors.centerIn: parent
                    text:            root.initials
                    color:           root.accentColor
                    font.pixelSize:  20
                    font.bold:       true
                }
            }

            // Name + description
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3

                // Project label
                Text {
                    text:            root.projectName
                    color:           Style.textSecondary
                    font.pixelSize:  Style.fontXs
                    font.letterSpacing: 0.4
                }

                // Context name
                Text {
                    Layout.fillWidth: true
                    text:            root.contextName
                    color:           Style.textPrimary
                    font.pixelSize:  Style.fontLg
                    font.bold:       true
                    elide:           Text.ElideRight
                }

                // Description
                Text {
                    Layout.fillWidth: true
                    text:            root.description
                    color:           Style.textSecondary
                    font.pixelSize:  Style.fontMd
                    wrapMode:        Text.WordWrap
                    maximumLineCount: 2
                    elide:           Text.ElideRight
                }
            }

            // Launch badge (top-right)
            Rectangle {
                Layout.alignment: Qt.AlignTop
                height:       22
                width:        badgeText_.implicitWidth + 16
                radius:       11
                color:        Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.14)
                border.width: 1
                border.color: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.40)

                Text {
                    id: badgeText_
                    anchors.centerIn: parent
                    text:            Style.launchLabel(root.launchTarget)
                    color:           root.accentColor
                    font.pixelSize:  Style.fontXs
                    font.bold:       true
                }
            }
        }

        // ── Separator ─────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: Style.border }

        // Package chips row
        Item {
            Layout.fillWidth:    true
            Layout.topMargin:    Style.sm
            Layout.bottomMargin: Style.sm
            Layout.leftMargin:   Style.lg
            Layout.rightMargin:  Style.lg
            height: 26

            Flickable {
                anchors.fill:        parent
                contentWidth:        chipRow_.implicitWidth
                flickableDirection:  Flickable.HorizontalFlick
                clip:                true

                Row {
                    id: chipRow_
                    spacing: 4
                    anchors.verticalCenter: parent.verticalCenter

                    Repeater {
                        model: root.packageList

                        Rectangle {
                            height:       22
                            width:        chip_.implicitWidth + 12
                            radius:       11
                            color:        Style.elevated
                            border.width: 1
                            border.color: Style.borderBright
                            anchors.verticalCenter: parent.verticalCenter

                            Text {
                                id: chip_
                                anchors.centerIn: parent
                                text:            modelData
                                color:           Style.textSecondary
                                font.pixelSize:  Style.fontXs
                                font.family:     "Consolas, Courier New, monospace"
                            }
                        }
                    }

                    // Empty state
                    Text {
                        visible:         root.packageList.length === 0
                        text:            "No packages"
                        color:           Style.textDisabled
                        font.pixelSize:  Style.fontXs
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        // ── Separator ─────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: Style.border }

        // Action buttons
        RowLayout {
            Layout.fillWidth:    true
            Layout.leftMargin:   Style.sm
            Layout.rightMargin:  Style.sm
            Layout.topMargin:    Style.sm
            Layout.bottomMargin: Style.sm
            spacing: Style.xs

            CardButton { icon: "✎"; label: "Info";     onClicked: root.editInfoRequested()     }
            CardButton { icon: "⊟"; label: "Packages"; onClicked: root.editPackagesRequested() }
            CardButton { icon: "◎"; label: "Preview";  onClicked: root.previewRequested()      }

            Item { Layout.fillWidth: true }

            CardButton { icon: "▶"; label: "Launch"; accent: true; onClicked: root.launchRequested() }
        }
    }
}
