# rez-manager — Design Reference

> This document is the authoritative design reference for AI agents and contributors.
> It describes UI windows, data structures, and file conventions for the project.

---

## Project Purpose

`rez-manager` is a PySide6/QML GUI application that wraps the Rez CLI/Python API.
It lets users create, configure, and launch Rez environments (contexts) per project
without needing to use the command line.

---

## Window / View Inventory

### 1. Main Window — Project & Context Manager

**Layout:** Two-panel horizontal split.

#### Left Panel — Project List

- Displays all projects as a scrollable list.
- Each item shows: project **name** + **thumbnail image**.
- Toolbar buttons: **Add**, **Delete**, **Edit**, **Refresh**.

#### Right Panel — Context List

Displays the Rez contexts belonging to the selected project.
Each context is rendered as a **card** containing:

| Field | Description |
|---|---|
| Project | Parent project name |
| Name | Context name |
| Description | Short text description |
| Thumbnail | Image for the context |
| Launch target | App to launch: Blender, Maya, Houdini, Nuke, NukeX, Shell, Custom, … |
| Packages (scrollable) | Single-line scrollable chip list of package requests |
| Actions | Edit Context Info · Edit Packages · Preview Env · Launch |

Outside the card list: **Add**, **Delete**, **Duplicate** buttons for contexts.

---

### 2. Settings Window

Opened from the main menu bar.

| Setting | Type | Description |
|---|---|---|
| Package repositories | List of paths | Multiple directories, each treated as a named group (folder name = group label). Example groups: `maya`, `houdini`. |
| Contexts location | Directory path | Root folder where context data is stored on disk. |

---

### 3. Package Manager Window (Dependency Editor)

Opens when "Edit Packages" is clicked on a context card.

**Layout:** Three-panel horizontal split + header + footer.

#### Header
Shows current **project name** and **context name**.

#### Left Panel — Current Package Requests
- List of packages already added to this context.
- Each row shows: package name + resolved/requested version.

#### Center Panel — Repository Browser (Tree View)
- Tree view grouping all configured repositories.
- Repository node label format: `folder_name [dir_path]`
- Children: package names only (no versions).

#### Right Panel — Package Detail Form
Shows info for the package selected in the center tree:

| Field | Widget |
|---|---|
| Package name | Label |
| Version | ComboBox (all available versions) |
| Description | Read-only text |
| Requires | List of transitive dependencies |
| Variants | List of available variants |
| Tools | List of tools provided by this package |
| Python code | Read-only display of `package.py` statements |

#### Add Button (prominent)
Adds the version selected in the right panel to the left panel's request list.

#### Footer
- **Left:** "Preview Resolve" button · "Launch Console" button (for debugging).
- **Right:** "Save" button.

---

### 4. Context Preview Window

Read-only inspection of a resolved context. Shows:

- Available tool commands.
- Resolved dependency list (full package versions after solve).
- All environment variables set by the context.

---

### 5. Context Editor Window (Info / Settings)

Opens on **Add Context** or **Edit Context Info**.

Fields:

| Field | Widget |
|---|---|
| Name | Text input |
| Project | Dropdown / selector |
| Description | Text area |
| Thumbnail | Image picker |
| Launch target | Dropdown (Blender, Maya, Houdini, Nuke, NukeX, Shell, Custom) |
| Custom command | Text input (visible only when Launch = Custom) |

---

## On-Disk Data Layout

All context data lives under the configured **contexts location** directory:

```
<contexts_location>/
└── <project_name>/           # One folder per project
    └── <context_name>/       # One folder per context
        ├── context.rxt       # Rez context file (serialized ResolvedContext)
        ├── meta.json         # Extra metadata (see schema below)
        └── thumbnail.png     # Optional thumbnail image
```

### `meta.json` schema

```json
{
  "name": "string",
  "description": "string",
  "launch_target": "Blender | Maya | Houdini | Nuke | NukeX | Shell | Custom",
  "custom_command": "string | null",
  "builtin_thumbnail_source": "qrc path string | null",
  "packages": ["pkg_name>=version", "..."]
}
```

---

## Architecture

```
src/rez_manager/
├── __main__.py          # Entry point: creates QApplication, loads QML
├── app.py               # QApplication subclass; registers QML types
├── adapter/             # Thin wrapper around Rez and filesystem adapters
│   ├── context.py       # ResolvedContext creation, serialization, preview
│   └── packages.py      # Repository discovery, package search/query
├── persistence/         # Generic filesystem persistence and path helpers
│   ├── app_paths.py     # Config/data path resolution
│   ├── settings_store.py
│   ├── project_store.py
│   └── context_store.py
├── models/              # Plain Python data models (dataclasses / Pydantic)
│   ├── project.py       # Project dataclass
│   └── rez_context.py   # ContextMeta, RezContext dataclasses
├── ui/                  # PySide6 QObject subclasses exposed to QML
│   ├── main_window.py   # MainWindowController
│   ├── settings_window.py
│   ├── package_manager.py
│   ├── context_preview.py
│   └── context_editor.py
└── qml/                 # QML UI files
    ├── main.qml         # Root QML; loads initial window
    ├── DarkRezStyle/    # Custom Styles
    ├── components/      # Reusable QML components (ContextCard, etc.)
    └── windows/         # Top-level window QML files
```

### Layer Rules

1. **adapter/** must be the only layer that imports from `rez.*`.
2. **models/** must not import from `rez.*` or PySide6.
3. **persistence/** owns generic filesystem/path persistence and must not import from `rez.*` or PySide6.
4. **ui/** exposes `@Property`, `@Slot`, `Signal` to QML and should prefer the model API over
   low-level persistence helpers.
5. **qml/** only communicates with **ui/** through registered QML types and signals.

---

## Tech Stack Quick Reference

| Tool | Role |
|---|---|
| Python ≥ 3.11 | Language |
| PySide6 ≥ 6.7 | Qt bindings + QML engine |
| QML | Declarative UI |
| rez ≥ 3.0 | Environment management backend |
| uv | Package manager & virtual environment |
| ruff | Linter and formatter |
| pytest | Test runner |

### Code Conventions

- **All source code and comments must be in English.**
- UI display strings use a separate i18n/translation layer (not hardcoded).
- Line length: 100 characters.
- Use `uv run` instead of calling `python` directly.
- Use `uvx ruff` or `uv run ruff` for linting.
