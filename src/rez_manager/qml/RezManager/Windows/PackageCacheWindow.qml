pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RezManager
import ".."
import "../Components"

// Package Cache Viewer — inspect and manage locally cached Rez packages.
Window {
    id: root
    title: qsTr("Package Cache")
    width: 860
    height: 600
    minimumWidth: 600
    minimumHeight: 400
    color: Style.bg
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

    property PackageCacheController cacheController: null

    // Context menu state
    property string contextMenuPackageName: ""
    property string contextMenuHandleJson: ""
    property string contextActionSource: "" // "variant" | "package"

    readonly property string effectiveCachePath: {
        if (!cacheController) return "";
        const p = cacheController.cachePath;
        return p.length > 0 ? p : cacheController.cachePathPlaceholder;
    }

    // ── Header area ──────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Toolbar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 48
            color: Style.surface

            RowLayout {
                anchors {
                    fill: parent
                    leftMargin: Style.lg
                    rightMargin: Style.lg
                }
                spacing: Style.sm

                Text {
                    text: qsTr("Cache Location:")
                    color: Style.textSecondary
                    font.pixelSize: Style.fontSm
                }
                Text {
                    Layout.fillWidth: true
                    text: root.effectiveCachePath
                    color: Style.textPrimary
                    font.pixelSize: Style.fontSm
                    font.family: "Consolas, Courier New, monospace"
                    elide: Text.ElideLeft
                }
                Item { Layout.fillWidth: true }
                CardButton {
                    glyph: "\u25B6"
                    label: qsTr("Reveal")
                    onClicked: {
                        if (cacheController && root.effectiveCachePath.length > 0)
                            cacheController.revealInExplorer(root.effectiveCachePath);
                    }
                }
                CardButton {
                    glyph: "\u21BB"
                    label: qsTr("Refresh")
                    onClicked: { if (cacheController) cacheController.refresh(); }
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width; height: 1; color: Style.border
            }
        }

        // Disabled banner
        Rectangle {
            Layout.fillWidth: true
            visible: cacheController ? !cacheController.cacheEnabled : false
            implicitHeight: visible ? 32 : 0
            color: Qt.rgba(Style.warning.r, Style.warning.g, Style.warning.b, 0.12)

            Text {
                anchors.centerIn: parent
                text: qsTr("Package cache is disabled. Enable it in Settings.")
                color: Style.warning
                font.pixelSize: Style.fontSm
            }
        }

        // Search / Filter
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 44
            color: "transparent"

            TextField {
                id: filterField_
                anchors {
                    left: parent.left; leftMargin: Style.lg
                    right: parent.right; rightMargin: Style.lg
                    verticalCenter: parent.verticalCenter
                }
                implicitHeight: 28
                placeholderText: qsTr("Filter by package name\u2026")
                onTextChanged: {
                    if (cacheController && cacheController.variantModel)
                        cacheController.variantModel.setFilter(text);
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width; height: 1; color: Style.border
            }
        }

        // ── Table view ───────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Style.bg

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Header
                HorizontalHeaderView {
                    id: header
                    Layout.fillWidth: true
                    syncView: treeView
                    clip: true

                    delegate: Rectangle {
                        implicitHeight: 28
                        color: Style.surface

                        Text {
                            anchors.centerIn: parent
                            text: {
                                const col = model.index;
                                if (col === 0) return qsTr("Variant");
                                if (col === 1) return qsTr("Status");
                                return qsTr("Source Path");
                            }
                            color: Style.textSecondary
                            font.pixelSize: Style.fontSm
                            font.bold: true
                        }

                        Rectangle {
                            anchors.right: parent.right
                            width: 1; height: parent.height
                            color: Style.border
                        }
                    }
                }

                // Tree rows + overlay stack
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    TreeView {
                        id: treeView
                        anchors.fill: parent
                        clip: true
                        enabled: cacheController ? cacheController.cacheEnabled : false
                        model: cacheController ? cacheController.variantModel : null
                        columnWidthProvider: function (column) {
                            if (column === 0) return 220;
                            if (column === 1) return 130;
                            return Math.max(150, treeView.width - 220 - 130);
                        }

                        delegate: Rectangle {
                            id: delegateRoot_
                            required property TreeView treeView
                            required property bool expanded
                            required property bool hasChildren
                            required property int depth
                            required property int row
                            required property int column
                            required property string nodeType
                            required property string label
                            required property string statusLabel
                            required property string sourcePath
                            required property int statusCode
                            required property string handleJson
                            required property string packageName

                            readonly property bool isPackage: nodeType === "package"
                            readonly property bool isVariant: nodeType === "variant"

                            implicitWidth: treeView.width
                            implicitHeight: isPackage ? 34 : 28
                            color: hoverHandler_.hovered ? Qt.rgba(1, 1, 1, 0.03) : "transparent"

                            Behavior on color { ColorAnimation { duration: 80 } }

                            // Column 0: expand toggle + label
                            RowLayout {
                                visible: column === 0
                                anchors {
                                    fill: parent
                                    leftMargin: isPackage ? Style.sm : Style.sm + Style.lg
                                    rightMargin: Style.md
                                }
                                spacing: Style.xs

                                Text {
                                    visible: isPackage
                                    text: expanded ? "\u25BE" : "\u25B8"
                                    color: Style.accent
                                    font.pixelSize: Style.fontXs
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                Rectangle {
                                    visible: isVariant
                                    implicitWidth: 4; implicitHeight: 4
                                    radius: 2
                                    color: Style.textDisabled
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: label
                                    color: isPackage ? Style.textPrimary : Style.textSecondary
                                    font.pixelSize: isPackage ? Style.fontSm : Style.fontMd
                                    font.bold: isPackage
                                    font.family: isPackage ? font.family : "Consolas, Courier New, monospace"
                                    elide: Text.ElideRight
                                }
                            }

                            // Column 1: status badge
                            RowLayout {
                                visible: column === 1
                                anchors {
                                    fill: parent
                                    leftMargin: Style.md
                                    rightMargin: Style.md
                                }
                                spacing: Style.xs

                                Rectangle {
                                    visible: isVariant
                                    implicitWidth: 8; implicitHeight: 8
                                    radius: 4
                                    color: {
                                        if (statusCode === 1) return Style.success;
                                        if (statusCode === 3) return Style.warning;
                                        if (statusCode === 4) return Style.error;
                                        return Style.textDisabled;
                                    }
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                Text {
                                    visible: isVariant
                                    text: statusLabel
                                    color: Style.textSecondary
                                    font.pixelSize: Style.fontMd
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                Text {
                                    visible: isPackage && statusLabel.length > 0
                                    text: statusLabel
                                    color: Style.textDisabled
                                    font.pixelSize: Style.fontXs
                                    font.italic: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                            }

                            // Column 2: source path
                            Text {
                                visible: column === 2 && isVariant
                                anchors {
                                    fill: parent
                                    leftMargin: Style.md
                                    rightMargin: Style.md
                                }
                                text: sourcePath
                                color: Style.textDisabled
                                font.pixelSize: Style.fontSm
                                font.family: "Consolas, Courier New, monospace"
                                elide: Text.ElideLeft
                                verticalAlignment: Text.AlignVCenter
                            }

                            HoverHandler {
                                id: hoverHandler_
                                cursorShape: Qt.PointingHandCursor
                            }

                            TapHandler {
                                gesturePolicy: TapHandler.WithinBounds
                                acceptedButtons: Qt.LeftButton
                                onTapped: {
                                    if (isPackage) {
                                        if (treeView.isExpanded(row))
                                            treeView.collapse(row);
                                        else
                                            treeView.expand(row);
                                    }
                                }
                            }

                            TapHandler {
                                gesturePolicy: TapHandler.WithinBounds
                                acceptedButtons: Qt.RightButton
                                onTapped: function (eventPoint) {
                                    root.contextMenuHandleJson = handleJson;
                                    root.contextMenuPackageName = packageName;
                                    root.contextActionSource = isVariant ? "variant" : "package";
                                    contextMenu_.popup(delegateRoot_, eventPoint.position.x, eventPoint.position.y);
                                }
                            }

                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width; height: isPackage ? 1 : 0
                                color: Style.border
                            }
                        }
                    }

                    // Loading overlay
                    Rectangle {
                        anchors.fill: parent
                        visible: cacheController ? cacheController.isLoading : false
                        color: Qt.rgba(Style.bg.r, Style.bg.g, Style.bg.b, 0.6)

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: Style.sm

                            BusyIndicator { running: parent.visible }
                            Text {
                                text: qsTr("Scanning cache\u2026")
                                color: Style.textSecondary
                                font.pixelSize: Style.fontMd
                            }
                        }
                    }

                    // Empty state
                    Text {
                        anchors.centerIn: parent
                        visible: treeView.rows === 0 && !(cacheController ? cacheController.isLoading : false)
                        text: filterField_.text.length > 0
                            ? qsTr("No matching cached packages.")
                            : qsTr("No packages cached yet.\nResolve a context to populate the cache.")
                        color: Style.textSecondary
                        font.pixelSize: Style.fontMd
                        horizontalAlignment: Text.AlignHCenter
                        lineHeight: 1.5
                    }
                }
            }
        }

        // ── Status bar ────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 28
            color: Style.surface
            Rectangle {
                anchors.top: parent.top
                width: parent.width; height: 1; color: Style.border
            }

            Text {
                anchors {
                    left: parent.left; leftMargin: Style.lg
                    verticalCenter: parent.verticalCenter
                }
                text: {
                    if (!cacheController) return "";
                    const count = cacheController.totalVariants;
                    if (count === 0) return qsTr("No cached variants");
                    return qsTr("%n variant(s) cached", "", count);
                }
                color: Style.textDisabled
                font.pixelSize: Style.fontXs
            }
        }
    }

    // ── Context menu ─────────────────────────────────────────────
    Menu {
        id: contextMenu_

        MenuItem {
            text: qsTr("Delete this variant")
            enabled: root.contextActionSource === "variant"
            onTriggered: {
                if (!root.cacheController || !root.contextMenuHandleJson)
                    return;
                root.cacheController.deleteVariant(root.contextMenuHandleJson);
            }
        }
        MenuItem {
            text: qsTr("Delete all variants of \"%1\"").arg(root.contextMenuPackageName)
            enabled: root.contextMenuPackageName.length > 0
            onTriggered: {
                if (!root.cacheController || !root.contextMenuPackageName)
                    return;
                root.cacheController.deletePackage(root.contextMenuPackageName);
            }
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Reveal in File Explorer")
            onTriggered: {
                if (!root.cacheController)
                    return;
                const path = root.contextActionSource === "variant"
                    ? root.effectiveCachePath
                    : root.effectiveCachePath;
                if (path.length > 0)
                    root.cacheController.revealInExplorer(path);
            }
        }
        MenuItem {
            text: qsTr("Copy path to clipboard")
            onTriggered: {
                const path = root.contextActionSource === "variant"
                    ? root.effectiveCachePath
                    : root.effectiveCachePath;
                clipboardProxy_.text = path;
                clipboardProxy_.selectAll();
                clipboardProxy_.copy();
                clipboardProxy_.deselect();
            }
        }
    }

    TextEdit {
        id: clipboardProxy_
        visible: false
    }

    Component.onCompleted: {
        if (cacheController)
            cacheController.refresh();
    }
}
