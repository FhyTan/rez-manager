pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Dialog {
    id: root
    title: qsTr("About rez-manager")
    modal: true
    width: 640
    height: 620
    padding: Style.xl

    property string repositoryUrl: "https://github.com/FhyTan/rez-manager"
    property string licenseName: "MIT"
    property string licenseText: qsTr("MIT License\n\n" + "Copyright (c) 2026 FhyTan\n\n" + "Permission is hereby granted, free of charge, to any person obtaining a copy " + "of this software and associated documentation files (the \"Software\"), to deal " + "in the Software without restriction, including without limitation the rights " + "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell " + "copies of the Software, and to permit persons to whom the Software is " + "furnished to do so, subject to the following conditions:\n\n" + "The above copyright notice and this permission notice shall be included in all " + "copies or substantial portions of the Software.\n\n" + "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR " + "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, " + "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE " + "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER " + "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, " + "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE " + "SOFTWARE.")
    signal githubRequested

    standardButtons: Dialog.Close
    onRejected: root.close()

    contentItem: ColumnLayout {
        spacing: Style.md

        Text {
            text: qsTr("rez-manager")
            color: Style.textPrimary
            font.pixelSize: Style.fontXl
            font.bold: true
        }

        Text {
            text: qsTr("Version %1").arg(Qt.application.version)
            color: Style.textSecondary
            font.pixelSize: Style.fontMd
        }

        Text {
            Layout.fillWidth: true
            text: qsTr("A desktop GUI for managing Rez package environments.")
            color: Style.textSecondary
            font.pixelSize: Style.fontMd
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: repoColumn_.implicitHeight + Style.md * 2
            radius: Style.radius
            color: Style.elevated
            border.width: 1
            border.color: Style.border

            ColumnLayout {
                id: repoColumn_
                anchors.fill: parent
                anchors.margins: Style.md
                spacing: Style.xs

                Text {
                    text: qsTr("Repository")
                    color: Style.textSecondary
                    font.pixelSize: Style.fontSm
                }

                Text {
                    Layout.fillWidth: true
                    text: root.repositoryUrl
                    color: Style.accent
                    font.pixelSize: Style.fontMd
                    wrapMode: Text.WrapAnywhere

                    TapHandler {
                        gesturePolicy: TapHandler.WithinBounds
                        onTapped: root.githubRequested()
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Style.radius
            color: Style.elevated
            border.width: 1
            border.color: Style.border

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Style.md
                spacing: Style.sm

                Text {
                    text: qsTr("License: ") + root.licenseName
                    color: Style.textPrimary
                    font.pixelSize: Style.fontMd
                    font.bold: true
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    Text {
                        width: parent.width
                        text: root.licenseText
                        color: Style.textSecondary
                        font.pixelSize: Style.fontSm
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }
}
