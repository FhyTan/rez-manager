import QtQuick 2.15
import QtQuick.Controls 2.15
import "components"
import "DarkRezStyle"
import "windows"

ApplicationWindow {
    id: root

    visible: true
    width: 800
    height: 600

    ComboBox {
        id: combo
        model: ["Option 1", "Option 2", "Option 3"]
        currentIndex: 0
    }
}

// ContextEditorDialog {
//     id: contextEditorDialog
// }

// Button {
//     text: "Open Context Editor"
//     anchors.centerIn: parent
//     onClicked: contextEditorDialog.open()
// }
// }

// PackageDetailPanel {
//     selectedPkgName: "test_pkg"
//     pkgDetail: {
//         "name": "test_pkg",
//         "versions": ["1.0.0", "1.1.0", "2.0.0"],
//         "description": "This is a test package.long long long long long description text to test the UI layout and text wrapping capabilities of the detail panel.",
//         "requires": [""],
//         "variants": ["long long long long long variant1", "variant2"],
//         "tools": ["long long long long long tool1", "tool2"],
//         "code": "def build():\n    print('Building test_pkg')"
//     }
// }
