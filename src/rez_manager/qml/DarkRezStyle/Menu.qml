import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import ".."

T.Menu {
    id: control

    property int minimumWidth: 176

    implicitWidth: Math.max(
        minimumWidth,
        implicitBackgroundWidth + leftInset + rightInset,
        implicitContentWidth + leftPadding + rightPadding
    )
    implicitHeight: Math.max(
        implicitBackgroundHeight + topInset + bottomInset,
        implicitContentHeight + topPadding + bottomPadding
    )

    modal: false
    dim: false
    margins: Style.sm
    overlap: 1
    padding: Style.xs
    topPadding: Style.xs
    bottomPadding: Style.xs
    leftPadding: Style.xs
    rightPadding: Style.xs
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    enter: Transition {
        ParallelAnimation {
            NumberAnimation {
                property: "opacity"
                from: 0.0
                to: 1.0
                duration: 120
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                property: "scale"
                from: 0.96
                to: 1.0
                duration: 140
                easing.type: Easing.OutCubic
            }
        }
    }

    exit: Transition {
        ParallelAnimation {
            NumberAnimation {
                property: "opacity"
                from: 1.0
                to: 0.0
                duration: 90
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                property: "scale"
                from: 1.0
                to: 0.98
                duration: 90
                easing.type: Easing.OutCubic
            }
        }
    }

    background: Rectangle {
        implicitWidth: control.minimumWidth
        implicitHeight: 40
        radius: Style.radius
        color: Style.elevated
        border.width: 1
        border.color: Style.borderBright
        opacity: 0.98
    }

    contentItem: ListView {
        implicitHeight: contentHeight
        model: control.contentModel
        interactive: Window.window
            ? contentHeight + control.topPadding + control.bottomPadding > control.height
            : false
        clip: true
        currentIndex: control.currentIndex

        ScrollIndicator.vertical: ScrollIndicator {}
    }
}