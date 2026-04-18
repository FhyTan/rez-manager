import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property var packageDetail: null

    signal detailVersionSelected(int index)
    signal addPackageRequested(string pkgName, string version)

    readonly property var versions: root.packageDetail ? root.packageDetail.versions : []
    readonly property string selectedVersion: root.packageDetail ? root.packageDetail.selectedVersion : ""

    color: Style.surface

    component DetailBox: ColumnLayout {
        id: detailBox_
        required property string title
        required property string body
        property bool monospace: false
        property bool codeStyle: false

        Layout.fillWidth: true
        spacing: Style.xs

        Text {
            text: detailBox_.title
            color: Style.textSecondary
            font.pixelSize: Style.fontXs
            font.bold: true
            font.letterSpacing: 0.5
        }

        Rectangle {
            id: detailViewport_
            Layout.fillWidth: true
            Layout.preferredHeight: detailText_.implicitHeight + Style.sm * 2 + (detailHorizontalBar_.visible ? detailHorizontalBar_.implicitHeight + Style.sm : 0)
            radius: Style.radiusSm
            color: detailBox_.codeStyle ? Style.elevated : Style.card
            border.width: 1
            border.color: Style.border

            Flickable {
                id: detailFlick_
                anchors.fill: parent
                anchors.leftMargin: Style.sm
                anchors.rightMargin: Style.sm
                anchors.topMargin: Style.sm
                anchors.bottomMargin: Style.sm
                contentWidth: Math.max(detailText_.implicitWidth, width)
                contentHeight: detailText_.implicitHeight
                flickableDirection: Flickable.HorizontalFlick
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.horizontal: ScrollBar {
                    id: detailHorizontalBar_
                    policy: ScrollBar.AsNeeded
                }
                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AlwaysOff
                }

                TextEdit {
                    id: detailText_
                    readOnly: true
                    text: detailBox_.body.length > 0 ? detailBox_.body : "—"
                    color: detailBox_.body.length > 0 ? Style.textPrimary : Style.textDisabled
                    font.pixelSize: Style.fontSm
                    font.family: detailBox_.monospace ? "Consolas, Courier New, monospace" : font.family
                    wrapMode: Text.NoWrap
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 40
            color: "transparent"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: Style.md
                anchors.verticalCenter: parent.verticalCenter
                text: "Package Detail"
                color: Style.textSecondary
                font.pixelSize: Style.fontSm
                font.bold: true
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        ScrollView {
            id: detailScroll_
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: Style.lg
            visible: root.packageDetail && root.packageDetail.hasSelection

            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            ColumnLayout {
                width: detailScroll_.availableWidth
                spacing: Style.lg

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        Layout.fillWidth: true
                        text: root.packageDetail ? root.packageDetail.name : "—"
                        color: Style.textPrimary
                        font.pixelSize: Style.fontXl
                        font.bold: true
                        elide: Text.ElideRight
                    }

                    ComboBox {
                        Layout.preferredWidth: 132
                        model: root.versions
                        currentIndex: root.packageDetail ? root.packageDetail.selectedVersionIndex : -1
                        onActivated: root.detailVersionSelected(currentIndex)
                    }
                }

                CardButton {
                    Layout.fillWidth: true
                    implicitHeight: 38
                    label: "Add  " + (root.packageDetail ? root.packageDetail.name : "Package") + (root.selectedVersion.length > 0 ? "  " + root.selectedVersion : "")
                    accent: true
                    onClicked: root.addPackageRequested(root.packageDetail ? root.packageDetail.name : "", root.selectedVersion)
                }

                DetailBox {
                    title: "Description"
                    body: root.packageDetail ? root.packageDetail.description : ""
                }

                DetailBox {
                    title: "Requires"
                    body: root.packageDetail ? root.packageDetail.requires.join("\n") : ""
                    monospace: true
                }

                DetailBox {
                    title: "Variants"
                    body: root.packageDetail ? root.packageDetail.variants.join("\n") : ""
                    monospace: true
                }

                DetailBox {
                    title: "Tools"
                    body: root.packageDetail ? root.packageDetail.tools.join("\n") : ""
                    monospace: true
                }

                DetailBox {
                    title: "package.py"
                    body: root.packageDetail ? root.packageDetail.code : ""
                    monospace: true
                    codeStyle: true
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !root.packageDetail || !root.packageDetail.hasSelection

            ColumnLayout {
                anchors.centerIn: parent
                spacing: Style.md

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "⊟"
                    font.pixelSize: 40
                    color: Style.textDisabled
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Select a package to see details"
                    color: Style.textDisabled
                    font.pixelSize: Style.fontMd
                }
            }
        }
    }
}
