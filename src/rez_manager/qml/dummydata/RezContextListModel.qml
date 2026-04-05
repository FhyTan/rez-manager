// RezContextListModel.qml — dummy implementation of the Python RezContextListModel.
//
// Python equivalent (to be implemented in src/rez_manager/ui/):
//   class RezContextListModel(QAbstractListModel):
//       Roles: project (str), name (str), description (str), launchTarget (str), packages (str)
//
// Also exposes two JS helper functions that will eventually be replaced by a
// QSortFilterProxyModel or equivalent Python-side filtering mechanism.
//
// Replace by registering the Python class as QML type "RezContextListModel"
// and removing the dummydata import in main.qml.

import QtQuick 2.15

Item {
    id: root
    visible: false

    // ── Public API (mirrors Python model surface) ─────────────────────────────

    // Direct access to the underlying ListModel (same as Python model itself).
    property alias count: contextsModel_.count
    function get(i) { return contextsModel_.get(i) }

    // Filtering helpers — replace with QSortFilterProxyModel on the Python side.
    function filteredContexts(projectName) {
        var result = []
        for (var i = 0; i < contextsModel_.count; i++) {
            var c = contextsModel_.get(i)
            if (c.project === projectName) {
                result.push({
                    project:      c.project,
                    name:         c.name,
                    description:  c.description,
                    launchTarget: c.launchTarget,
                    packages:     c.packages
                })
            }
        }
        return result
    }

    function contextCountFor(projectName) {
        var count = 0
        for (var i = 0; i < contextsModel_.count; i++) {
            if (contextsModel_.get(i).project === projectName) count++
        }
        return count
    }

    // ── Dummy data ────────────────────────────────────────────────────────────

    ListModel {
        id: contextsModel_

        // VFX Pipeline
        ListElement {
            project:      "VFX Pipeline"
            name:         "Maya 2024 Base"
            description:  "Base Maya 2024 environment with Arnold renderer and USD support."
            launchTarget: "maya"
            packages:     "maya-2024,python-3.11,mtoa-5.3,usd-23.11,openexr-3.1"
        }
        ListElement {
            project:      "VFX Pipeline"
            name:         "Nuke 14 Comp"
            description:  "Compositing environment with Nuke 14, NukeX and OCIO 2 support."
            launchTarget: "custom"
            packages:     "nuke-14.0,python-3.10,nukex-14.0,ocio-2.2,ffmpeg-6.0"
        }
        ListElement {
            project:      "VFX Pipeline"
            name:         "Shell Dev"
            description:  "Development shell with Python tools and build utilities."
            launchTarget: "shell"
            packages:     "python-3.11,cmake-3.27,git-2.42,ninja-1.11,ruff-0.1"
        }

        // Maya Rigging
        ListElement {
            project:      "Maya Rigging"
            name:         "Rigging Tools"
            description:  "Full rigging environment with mGear, CGM tools and Pyblish."
            launchTarget: "maya"
            packages:     "maya-2024,python-3.11,mgear-4.1,cgm-2.0,pyblish-2.0,pyqt5-5.15"
        }
        ListElement {
            project:      "Maya Rigging"
            name:         "QC Validation"
            description:  "Quality control and validation toolchain."
            launchTarget: "shell"
            packages:     "python-3.11,pytest-7.4,mypy-1.5,ruff-0.1"
        }

        // Houdini FX
        ListElement {
            project:      "Houdini FX"
            name:         "Houdini 20.5"
            description:  "Standard Houdini FX environment with Karma renderer and MaterialX."
            launchTarget: "houdini"
            packages:     "houdini-20.5,python-3.11,karma-1.0,materialx-1.38"
        }
        ListElement {
            project:      "Houdini FX"
            name:         "Houdini + Redshift"
            description:  "Houdini environment with Redshift GPU renderer plugin."
            launchTarget: "houdini"
            packages:     "houdini-20.5,python-3.11,redshift-3.5,redshift-houdini-3.5"
        }

        // USD Pipeline
        ListElement {
            project:      "USD Pipeline"
            name:         "USD Tools"
            description:  "Universal Scene Description toolset for pipeline integration."
            launchTarget: "shell"
            packages:     "python-3.11,usd-23.11,hdstorm-23.11,materialx-1.38,openexr-3.1"
        }
    }
}
