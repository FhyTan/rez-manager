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

### 6. Package Cache Viewer Window

Opened from **File → Package Cache…** menu. A non-modal `Window` that displays the local Rez package cache contents.

**Layout:** Single-column vertical layout with header, search filter, and a multi-column TreeView grouped by package name.

#### Header Area

| Widget | Description |
|---|---|
| Cache path label + value | Current cache directory (from settings, or default) |
| "Reveal in Explorer" button | Opens cache directory in system file manager |
| "Refresh" button | Rescans cache asynchronously via `PackageCache.get_variants()` |
| Disabled banner (conditional) | Shown when package cache is disabled in settings |

#### Search / Filter

`TextField` with placeholder "Filter by package name…". Real-time filtering rebuilds the tree model with only matching packages.

#### Cached Variants Tree

**TreeView** with 3 columns, header provided by `HorizontalHeaderView` (sync'd with `syncView`):

| Column | Header | Initial width | Resizable |
|---|---|---|---|
| 0 | `Variant` | 220px | Yes |
| 1 | `Status` | 130px | Yes |
| 2 | `Source Path` | Stretch | Yes |

**Tree structure (two levels):**

```
Package node (depth 0)
├── render: "▾ package_name (N variants)"
├── col 1: (summary) "all cached" / "2 stalled"
├── col 2: (empty)
└── children: Variant nodes (depth 1)

Variant node (depth 1)
├── col 0: version[variant_index] (+requires)
├── col 1: status badge (colored dot + label)
└── col 2: source path (var.root)
```

**Variant display:** `var.qualified_name` with the `{package_name}-` prefix stripped (e.g., `arnold-7.3.1.0[]` → `7.3.1.0[]`), suffixed with `(+deps)` if `variant_requires` is non-empty.

**Status mapping:** `1` → "Cached" (green), `3` → "Copying…" (yellow), `4` → "Stalled" (red), `5` → "Pending" (gray).

#### Context Menus

| Target | Menu Items |
|---|---|
| Package node | "Delete all variants of [package]" / "Reveal in File Explorer" / "Copy path" |
| Variant node | "Delete this variant" / "Reveal in File Explorer" / "Copy path" |

#### Deletion Flow

1. User right-clicks → selects delete action
2. Controller calls `PackageCache.remove_variant(Variant)` (moves payload to remove dir)
3. Does **not** call `clean()` — the `rez-pkg-cache` daemon handles cleanup asynchronously
4. Tree refreshes automatically on success

#### Cache Path Handling

- Reads from `AppSettings.package_cache.path`
- If empty, falls back to `default_rez_package_caches_dir()`
- Creates the directory automatically (`mkdir(parents=True, exist_ok=True)`) before querying

#### Edge Cases

| Scenario | Behavior |
|---|---|
| Cache disabled | Banner "Package cache is disabled. Enable it in Settings." + disabled TreeView |
| Cache directory missing | Auto-created on refresh |
| No cached variants | Empty state: "No packages cached yet. Resolve a context to populate the cache." |
| Filter matches nothing | "No matching cached packages." |
| Delete fails (variant being copied) | Error toast via AppErrorHub |

#### Rez API Reference

```python
from rez.package_cache import PackageCache

cache = PackageCache(path)
cache.get_variants()        # → list[(Variant, cache_path, status)]
cache.remove_variant(var)   # → status_code (VARIANT_REMOVED, etc.)

# Variant properties used:
#   var.qualified_name       → "arnold-7.3.1.0[]"
#   var.root                 → "D:\...\arnold\7.3.1.0"
#   var.version              → version object
#   var.index                → None | int
#   var.variant_requires     → list[PackageRequest]
```

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
