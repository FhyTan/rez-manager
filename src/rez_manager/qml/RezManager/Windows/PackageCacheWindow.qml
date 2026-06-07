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
    readonly property string errorTarget_: "package-cache"
    AppErrorTarget.errorTarget: root.errorTarget_

    signal openLogsRequested

    PackageCacheController {
        id: cacheController_
    }

    // Context menu state
    property string contextMenuPackageName: ""
    property string contextMenuHandleJson: ""
    property string contextActionSource: "" // "variant" | "package"

    readonly property string effectiveCachePath: {
        const p = cacheController_.cachePath;
        return p.length > 0 ? p : cacheController_.cachePathPlaceholder;
    }

    function showStatus(message, isError) {
        statusToast_.show(message, isError ? Style.error : Style.success);
    }

    Connections {
        target: AppErrorHub // qmllint disable incompatible-type
        function onErrorOccurred(message, target) {
            if (target === root.errorTarget_ && root.visible)
                statusToast_.show(message, Style.error);
        }
    }

    Connections {
        target: cacheController_
        function onLoadingChanged() {
            if (!cacheController_.isLoading)
                treeView_.expandRecursively();
        }
    }

    StatusToast {
        id: statusToast_
        z: 999
        onActivated: root.openLogsRequested()
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
                Item {
                    Layout.fillWidth: true
                }
                CardButton {
                    glyph: "\u{1F5C1}"
                    label: qsTr("Reveal")
                    onClicked: {
                        if (root.effectiveCachePath.length > 0)
                            cacheController_.revealInExplorer(root.effectiveCachePath);
                    }
                }
                CardButton {
                    glyph: "\u21BB"
                    label: qsTr("Refresh")
                    onClicked: cacheController_.refresh()
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
            }
        }

        // Disabled banner
        Rectangle {
            Layout.fillWidth: true
            visible: !cacheController_.cacheEnabled
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
            implicitHeight: 48
            color: "transparent"

            TextField {
                id: filterField_
                anchors {
                    left: parent.left
                    leftMargin: Style.lg
                    right: parent.right
                    rightMargin: Style.lg
                    verticalCenter: parent.verticalCenter
                }
                placeholderText: qsTr("Filter by package name\u2026")
                onTextChanged: {
                    var m = cacheController_.variantModel;
                    if (m)
                        m.setFilter(text);
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Style.border
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
                    syncView: treeView_
                    clip: true
                    onWidthChanged: treeView_.forceLayout()

                    model: [qsTr("Variant"), qsTr("Status"), qsTr("Source Path")]

                    delegate: Rectangle {
                        implicitHeight: 28
                        color: Style.surface
                        required property string modelData

                        Text {
                            anchors.centerIn: parent
                            text: parent.modelData
                            color: Style.textSecondary
                            font.pixelSize: Style.fontSm
                            font.bold: true
                        }

                        Rectangle {
                            anchors.right: parent.right
                            width: 1
                            height: parent.height
                            color: Style.border
                        }
                    }
                }

                // Tree rows + overlay stack
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    TreeView {
                        id: treeView_
                        anchors.fill: parent
                        clip: true
                        enabled: cacheController_.cacheEnabled
                        model: cacheController_.variantModel
                        selectionBehavior: TableView.SelectRows
                        selectionMode: TableView.SingleSelection
                        selectionModel: ItemSelectionModel {}

                        columnWidthProvider: function (column) {
                            const lastCol = treeView_.columns - 1;
                            if (column === lastCol) {
                                let used = 0;
                                for (let i = 0; i < lastCol; ++i)
                                    used += treeView_.columnWidth(i);
                                return treeView_.width - used;
                            }
                            const w = treeView_.explicitColumnWidth(column);
                            return Math.max(w, column === 0 ? 220 : 130);
                        }

                        onWidthChanged: treeView_.forceLayout()

                        delegate: TreeViewDelegate {
                            id: delegateRoot_
                            required property int column
                            required property string nodeType
                            required property string label
                            required property string statusLabel
                            required property string sourcePath
                            required property int statusCode
                            required property string handleJson
                            required property string packageName

                            readonly property bool delegateIsPackage: nodeType === "package"
                            readonly property bool delegateIsVariant: nodeType === "variant"

                            implicitHeight: 34

                            contentItem: Item {
                                // Column 0: label
                                RowLayout {
                                    visible: delegateRoot_.column === 0
                                    anchors {
                                        fill: parent
                                        rightMargin: Style.md
                                    }
                                    spacing: Style.xs

                                    Rectangle {
                                        visible: delegateRoot_.delegateIsVariant
                                        implicitWidth: 4
                                        implicitHeight: 4
                                        radius: 2
                                        color: Style.textDisabled
                                        Layout.alignment: Qt.AlignVCenter
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: delegateRoot_.label
                                        color: Style.textPrimary
                                        font.pixelSize: Style.fontSm
                                        font.bold: delegateRoot_.delegateIsPackage
                                        elide: Text.ElideRight
                                    }
                                }

                                // Column 1: status badge
                                RowLayout {
                                    visible: delegateRoot_.column === 1
                                    anchors {
                                        fill: parent
                                        rightMargin: Style.md
                                    }
                                    spacing: Style.xs

                                    Rectangle {
                                        visible: delegateRoot_.delegateIsVariant
                                        implicitWidth: 8
                                        implicitHeight: 8
                                        radius: 4
                                        color: {
                                            if (delegateRoot_.statusCode === 1)
                                                return Style.success;
                                            if (delegateRoot_.statusCode === 3)
                                                return Style.warning;
                                            if (delegateRoot_.statusCode === 4)
                                                return Style.error;
                                            return Style.textDisabled;
                                        }
                                        Layout.alignment: Qt.AlignVCenter
                                    }

                                    Text {
                                        visible: delegateRoot_.delegateIsVariant
                                        Layout.fillWidth: true
                                        text: delegateRoot_.statusLabel
                                        color: Style.textSecondary
                                        font.pixelSize: Style.fontSm
                                        elide: Text.ElideRight
                                        Layout.alignment: Qt.AlignVCenter
                                    }

                                    Text {
                                        visible: delegateRoot_.delegateIsPackage && delegateRoot_.statusLabel.length > 0
                                        Layout.fillWidth: true
                                        text: delegateRoot_.statusLabel
                                        color: Style.textSecondary
                                        font.pixelSize: Style.fontSm
                                        font.italic: true
                                        elide: Text.ElideRight
                                        Layout.alignment: Qt.AlignVCenter
                                    }
                                }

                                // Column 2: source path
                                Text {
                                    visible: delegateRoot_.column === 2 && delegateRoot_.delegateIsVariant
                                    anchors {
                                        fill: parent
                                        leftMargin: Style.md
                                        rightMargin: Style.md
                                    }
                                    text: delegateRoot_.sourcePath
                                    color: Style.textSecondary
                                    font.pixelSize: Style.fontSm
                                    font.family: "Consolas, Courier New, monospace"
                                    elide: Text.ElideLeft
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            HoverHandler {
                                cursorShape: Qt.PointingHandCursor
                            }

                            TapHandler {
                                gesturePolicy: TapHandler.WithinBounds
                                acceptedButtons: Qt.RightButton
                                onTapped: function (eventPoint) {
                                    treeView_.selectionModel.setCurrentIndex(treeView_.index(delegateRoot_.row, 0), "SelectCurrent");
                                    root.contextMenuHandleJson = delegateRoot_.handleJson;
                                    root.contextMenuPackageName = delegateRoot_.packageName;
                                    root.contextActionSource = delegateRoot_.delegateIsVariant ? "variant" : "package";
                                    contextMenu_.popup(delegateRoot_, eventPoint.position.x, eventPoint.position.y);
                                }
                            }
                        }
                    }

                    // Loading overlay
                    Rectangle {
                        anchors.fill: parent
                        visible: cacheController_.isLoading
                        color: Qt.rgba(Style.bg.r, Style.bg.g, Style.bg.b, 0.6)

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: Style.sm

                            BusyIndicator {
                                running: parent.visible
                            }
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
                        visible: treeView_.rows === 0 && !cacheController_.isLoading
                        text: filterField_.text.length > 0 ? qsTr("No matching cached packages.") : qsTr("No packages cached yet.\nResolve a context to populate the cache.")
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
                width: parent.width
                height: 1
                color: Style.border
            }

            Text {
                anchors {
                    left: parent.left
                    leftMargin: Style.lg
                    verticalCenter: parent.verticalCenter
                }
                text: {
                    const count = cacheController_.totalVariants;
                    if (count === 0)
                        return qsTr("No cached variants");
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
                if (!root.contextMenuHandleJson)
                    return;
                cacheController_.deleteVariant(root.contextMenuHandleJson);
            }
        }
        MenuItem {
            text: qsTr("Delete all variants of \"%1\"").arg(root.contextMenuPackageName)
            enabled: root.contextMenuPackageName.length > 0
            onTriggered: {
                if (!root.contextMenuPackageName)
                    return;
                cacheController_.deletePackage(root.contextMenuPackageName);
            }
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Reveal in File Explorer")
            onTriggered: {
                if (root.effectiveCachePath.length > 0)
                    cacheController_.revealInExplorer(root.effectiveCachePath);
            }
        }
        MenuItem {
            text: qsTr("Copy path to clipboard")
            onTriggered: {
                clipboardProxy_.text = root.effectiveCachePath;
                clipboardProxy_.selectAll();
                clipboardProxy_.copy();
                clipboardProxy_.deselect();
            }
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Expand All")
            onTriggered: treeView_.expandRecursively()
        }
        MenuItem {
            text: qsTr("Collapse All")
            onTriggered: treeView_.collapseRecursively()
        }
    }

    TextEdit {
        id: clipboardProxy_
        visible: false
    }

    onVisibleChanged: {
        if (visible)
            cacheController_.refresh();     // ← every open
    }
}
