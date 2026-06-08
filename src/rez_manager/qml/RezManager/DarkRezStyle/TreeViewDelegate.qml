import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import ".."

T.TreeViewDelegate {
    id: control

    implicitWidth: leftMargin + __contentIndent + implicitContentWidth + rightPadding + rightMargin
    implicitHeight: Math.max(implicitBackgroundHeight, implicitContentHeight, implicitIndicatorHeight)

    indentation: indicator ? indicator.width : 12
    leftMargin: Style.sm
    rightMargin: Style.md
    spacing: Style.xs

    topPadding: 0
    bottomPadding: 0
    leftPadding: !control.mirrored ? leftMargin + __contentIndent : width - leftMargin - __contentIndent - implicitContentWidth

    highlighted: control.selected || control.current || ((control.treeView.selectionBehavior === TableView.SelectRows || control.treeView.selectionBehavior === TableView.SelectionDisabled) && control.row === control.treeView.currentRow)

    required property int row
    required property var model
    readonly property real __contentIndent: !isTreeNode ? 0 : (depth * indentation) + (indicator ? indicator.width + spacing : 0)

    indicator: Item {
        readonly property real __indent: control.leftMargin + (control.depth * control.indentation)
        x: !control.mirrored ? __indent : control.width - __indent - width
        y: (control.height - height) / 2
        implicitWidth: Math.max(arrow_.implicitWidth, 10)
        implicitHeight: 24

        ColorImage {
            id: arrow_
            anchors.centerIn: parent
            visible: control.hasChildren
            source: "qrc:/qt-project.org/imports/QtQuick/Controls/Fusion/images/arrow.png"
            color: Style.accent
            rotation: control.expanded ? 0 : (control.mirrored ? 90 : -90)
        }
    }

    background: Rectangle {
        color: control.highlighted ? Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.15) : "transparent"
        implicitHeight: 34

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: control.hasChildren ? 1 : 0
            color: Style.border
        }
    }

    contentItem: Item {}
}
