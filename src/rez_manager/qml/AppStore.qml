// AppStore.qml — Centralised application data store (dummy implementation).
//
// Exposes the same surface as the future Python-backed QObject:
//   • projects  : ListModel  — list of {name, avatarColor}
//   • contexts  : ListModel  — list of {project, name, description, launchTarget, packages}
//   • filteredContexts(projectName) → JS array
//   • contextCountFor(projectName)  → int
//
// To replace with real data: register a Python QObject under the name "AppStore"
// via qmlRegisterType / @QmlElement and expose the same properties + slots.

import QtQuick 2.15

Item {
    id: root
    visible: false

    // ── Public API ────────────────────────────────────────────────────────────

    property alias projects: projectsModel_
    property alias contexts: contextsModel_

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
        id: projectsModel_
        ListElement { name: "VFX Pipeline"; avatarColor: "#5F83FF" }
        ListElement { name: "Maya Rigging"; avatarColor: "#4DB880" }
        ListElement { name: "Houdini FX";   avatarColor: "#D98A38" }
        ListElement { name: "USD Pipeline"; avatarColor: "#8A58D8" }
    }

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
