# rez-manager — Project Guide

## Description

A PySide6/QML desktop GUI for managing [Rez](https://github.com/AcademySoftwareFoundation/rez) package environments. Users create projects, configure Rez contexts (package requests + versions), resolve them, and launch DCC tools (Blender, Maya, Houdini, Nuke, etc.) inside those environments.

## Architecture Layers (strict dependency rules)

```
src/rez_manager/
├── __main__.py          # Entry point
├── app.py               # QApplication factory, QML type registration
├── adapter/             # ONLY layer that imports rez.*
├── models/              # Pure dataclasses — NO rez.* / NO PySide6
├── persistence/         # Filesystem CRUD — NO rez.* / NO PySide6
├── ui/                  # QObject subclasses exposed to QML (Property, Slot, Signal)
└── qml/                 # Declarative QML views — communicates only via registered types
```

- `adapter/` ↔ PySide6: dependent on PySide6 `QThread` for async operations.
- `models/` must not import `rez.*` or `PySide6`.
- `persistence/` must not import `rez.*` or `PySide6`.
- `ui/` should prefer model API over low-level persistence helpers.

## Tech Stack

| Tool | Role |
|---|---|
| Python ≥ 3.11 | Language |
| PySide6 ≥ 6.9 | Qt bindings + QML engine |
| QML | Declarative UI |
| rez ≥ 3.0 | Environment management |
| uv | Package & venv management |
| ruff | Linter + formatter |
| pytest | Test runner |

## Key Conventions

- **All source code and comments must be in English.**
- **Line length:** 100 chars.
- Use `pathlib.Path` for filesystem paths — never raw `str` paths.
- Provide PEP 257 docstrings for public modules, classes, and functions. No obvious comments.
- Catch specific exceptions — no bare `except:`.
- Prefer Python 3.10+ syntax (`int | str`, `list[str]`, `match/case`).
- Use `from __future__ import annotations` when it improves forward references.
- Always specify `encoding="utf-8"` when reading/writing text files.

## QML / PySide6 Patterns

- QML is the declarative view layer only. Business logic, I/O, and state stay in Python.
- Python ↔ QML communication: `QObject` with `Signal`, `Property`, `Slot` — registered via `@QmlElement` and `@QmlSingleton`.
- Prefer unversioned QML imports (`import QtQuick`, `import QtQuick.Controls`).
- Use Pointer Handlers (`TapHandler`, `HoverHandler`, `DragHandler`) over `MouseArea`.
- Use `required property` for delegate inputs.
- Prefer declarative bindings over imperative `Component.onCompleted` assignments.
- Regenerate QML stubs after modifying Python QML types: `uv run pyside6-qml-stubgen src --out-dir ./qmltypes`.
- Run QML lint: `uv run pyside6-qmllint -I ./qmltypes <qml-files>`.
- Format QML: `uv run pyside6-qmlformat -i <qml-files>`.

## Useful Commands

```bash
uv run ruff check src tests     # Lint
uv run ruff format --check .    # Check formatting
uv run ruff format .            # Format
uv run pytest                   # Run tests
uv run pytest -v                # Verbose tests
uv run python -m rez_manager    # Run app
```

## On-Disk Data Layout (per context)

```
<contexts_location>/<project_name>/<context_name>/
├── context.rxt       # Serialized Rez ResolvedContext
├── meta.json         # JSON metadata (name, description, launch_target, packages, etc.)
└── thumbnail.png     # Optional thumbnail
```

## Exception Hierarchy

All custom exceptions live in `src/rez_manager/exceptions.py`. Base is `RezManagerError`, with subclasses for adapter errors (`RezAdapterError`, `RezResolveError`, `RezContextLoadError`, etc.).

## Tests

Mirror source layout under `tests/` (e.g., `tests/adapter/`, `tests/ui/`). Use pytest. Focus on observable behavior over implementation details.
