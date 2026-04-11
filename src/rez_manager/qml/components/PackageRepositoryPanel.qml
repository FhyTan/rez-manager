import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property var repoTree: []
    property int selectedRepoIndex: -1
    property int selectedPkgIndex: -1

    signal repositoryToggled(int index)
    signal packageSelected(int repoIndex, int pkgIndex)

    color: Style.bg

    component RepositorySection: ColumnLayout {
        id: repositorySection
        required property int repoIndex
        required property var repoData

        Layout.fillWidth: true
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 36
            color: headerHover_.hovered ? Style.elevated : Style.surface

            Behavior on color {
                ColorAnimation { duration: 80 }
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.sm
                anchors.rightMargin: Style.sm
                spacing: Style.xs

                Text {
                    text: root.selectedRepoIndex === repositorySection.repoIndex ? "▾" : "▸"
                    color: Style.accent
                    font.pixelSize: Style.fontXs
                    Layout.alignment: Qt.AlignVCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: repositorySection.repoData.label
                    color: Style.textPrimary
                    font.pixelSize: Style.fontSm
                    font.bold: true
                    elide: Text.ElideRight
                }
            }

            HoverHandler {
                id: headerHover_
                cursorShape: Qt.PointingHandCursor
            }

            TapHandler {
                acceptedButtons: Qt.LeftButton
                onTapped: root.repositoryToggled(repositorySection.repoIndex)
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        Repeater {
            model: root.selectedRepoIndex === repositorySection.repoIndex
                ? repositorySection.repoData.packages
                : []

            delegate: Rectangle {
                id: packageDelegate_
                required property string modelData
                required property int index

                Layout.fillWidth: true
                height: 32

                property bool isSelected: root.selectedRepoIndex === repositorySection.repoIndex
                    && root.selectedPkgIndex === index

                color: isSelected
                    ? Qt.rgba(Style.accent.r, Style.accent.g, Style.accent.b, 0.12)
                    : (packageHover_.hovered ? Style.elevated : "transparent")

                Behavior on color {
                    ColorAnimation { duration: 80 }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Style.xl
                    anchors.rightMargin: Style.md

                    Rectangle {
                        width: 4
                        height: 4
                        radius: 2
                        color: packageDelegate_.isSelected ? Style.accent : Style.textDisabled
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Text {
                        Layout.fillWidth: true
                        text: modelData
                        color: packageDelegate_.isSelected ? Style.accent : Style.textSecondary
                        font.pixelSize: Style.fontMd
                        font.family: "Consolas, Courier New, monospace"
                        elide: Text.ElideRight
                    }
                }

                HoverHandler {
                    id: packageHover_
                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onTapped: root.packageSelected(repositorySection.repoIndex, index)
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "transparent"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: Style.md
                anchors.verticalCenter: parent.verticalCenter
                text: "Package Repository"
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
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 0

                Repeater {
                    model: root.repoTree

                    delegate: RepositorySection {
                        required property int index
                        required property var modelData

                        repoIndex: index
                        repoData: modelData
                    }
                }
            }
        }
    }
}
