import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

// Context card — the primary display unit for a Rez context.
// Signals: editInfoRequested, editPackagesRequested, previewRequested, launchRequested
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

    // ── Internal ─────────────────────────────────────────────
    Style { id: s_ }

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

    property color accentColor: s_.launchColor(launchTarget)

    // ── Geometry ─────────────────────────────────────────────
    width:  365
    height: col_.implicitHeight + 3   // +3 for top accent strip
    radius: s_.radius

    color: hoverArea_.containsMouse ? s_.cardHover : s_.card
    Behavior on color { ColorAnimation { duration: 100 } }

    // ── Border ────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        radius:       parent.radius
        color:        "transparent"
        border.width: 1
        border.color: hoverArea_.containsMouse ? s_.borderBright : s_.border
    }

    // ── Top accent strip ─────────────────────────────────────
    Rectangle {
        id: strip_
        anchors.top:   parent.top
        anchors.left:  parent.left
        anchors.right: parent.right
        height: 3
        radius: s_.radius
        color:  root.accentColor
        // Flatten the bottom two corners of the strip
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left:   parent.left
            anchors.right:  parent.right
            height: s_.radius
            color:  parent.color
        }
    }

    // ── Hover capture ─────────────────────────────────────────
    MouseArea {
        id: hoverArea_
        anchors.fill:   parent
        hoverEnabled:   true
        acceptedButtons: Qt.NoButton
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
            Layout.topMargin:    s_.lg
            Layout.leftMargin:   s_.lg
            Layout.rightMargin:  s_.lg
            Layout.bottomMargin: s_.md
            spacing: s_.md

            // Avatar
            Rectangle {
                width:        58
                height:       58
                radius:       s_.radiusSm
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
                    color:           s_.textSecondary
                    font.pixelSize:  s_.fontXs
                    font.letterSpacing: 0.4
                }

                // Context name
                Text {
                    Layout.fillWidth: true
                    text:            root.contextName
                    color:           s_.textPrimary
                    font.pixelSize:  s_.fontLg
                    font.bold:       true
                    elide:           Text.ElideRight
                }

                // Description
                Text {
                    Layout.fillWidth: true
                    text:            root.description
                    color:           s_.textSecondary
                    font.pixelSize:  s_.fontMd
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
                    text:            s_.launchLabel(root.launchTarget)
                    color:           root.accentColor
                    font.pixelSize:  s_.fontXs
                    font.bold:       true
                }
            }
        }

        // ── Separator ─────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: s_.border }

        // Package chips row
        Item {
            Layout.fillWidth:    true
            Layout.topMargin:    s_.sm
            Layout.bottomMargin: s_.sm
            Layout.leftMargin:   s_.lg
            Layout.rightMargin:  s_.lg
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
                            color:        s_.elevated
                            border.width: 1
                            border.color: s_.borderBright
                            anchors.verticalCenter: parent.verticalCenter

                            Text {
                                id: chip_
                                anchors.centerIn: parent
                                text:            modelData
                                color:           s_.textSecondary
                                font.pixelSize:  s_.fontXs
                                font.family:     "Consolas, Courier New, monospace"
                            }
                        }
                    }

                    // Empty state
                    Text {
                        visible:         root.packageList.length === 0
                        text:            "No packages"
                        color:           s_.textDisabled
                        font.pixelSize:  s_.fontXs
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        // ── Separator ─────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: s_.border }

        // Action buttons
        RowLayout {
            Layout.fillWidth:    true
            Layout.leftMargin:   s_.sm
            Layout.rightMargin:  s_.sm
            Layout.topMargin:    s_.sm
            Layout.bottomMargin: s_.sm
            spacing: s_.xs

            CardButton { icon: "✎"; label: "Info";     onClicked: root.editInfoRequested()     }
            CardButton { icon: "⊟"; label: "Packages"; onClicked: root.editPackagesRequested() }
            CardButton { icon: "◎"; label: "Preview";  onClicked: root.previewRequested()      }

            Item { Layout.fillWidth: true }

            CardButton { icon: "▶"; label: "Launch"; accent: true; onClicked: root.launchRequested() }
        }
    }
}
