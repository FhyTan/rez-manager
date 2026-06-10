# rez-manager

[中文说明](./README.zh-CN.md)
[Changelog](./CHANGELOG.md)

A modernized GUI tool for managing [Rez](https://rez.readthedocs.io/en/stable/) package environments.

rez-manager provides a desktop UI for creating, editing, previewing, and launching Rez contexts
for DCC workflows.

## Current Limitations

- This application has only been tested on Windows. Other platforms are not supported yet.
- rez-manager does not create Rez packages. Users need to create and maintain packages manually
 according to the [Rez documentation](https://rez.readthedocs.io/en/stable/package_definition.html).

## Features

### Group your rez contexts by project

![group contexts by project](./images/group_contexts_by_project.gif)

### Launch DCC software by one click

![launch DCC software](./images/launch_dcc.gif)

### Select which DCC software to launch with each context

![select DCC software](./images/select_dcc.gif)

### Config the dependencies packages for each context

![config dependencies packages](./images/config_dependencies_packages.gif)

### Preview the resolved environment for each context

![preview resolved environment](./images/preview_resolved_environment.gif)

### Debug the context during packages configuration

![debug context](./images/debug_context.gif)

### Easy access the error logs when something goes wrong

![error logs](./images/error_logs.gif)

### Support package caching

When the Rez package is stored on a network shared drive with caching enabled, resolve or launch action will automatically cache the package locally in the background. On subsequent launches, the local cache will be used directly, significantly accelerating the startup process.

## Example Data

The [`./examples`](./examples) directory contains sample projects and Rez packages for trying the
application quickly. Point the app settings to those example directories to preview the main
features without preparing your own package repository first.

## Setup and Build

### Requirements

- [uv](https://docs.astral.sh/uv/)

`uv` will provision the required Python version from the project metadata when needed.

### Run from source

```bash
uv sync
uv run rez-manager
```

### Run from pre-built executable

Pre-built executables can be downloaded from the [Releases](https://github.com/FhyTan/rez-manager/releases) page.

### Build a desktop executable

```batch
.\build_scripts\build.bat
```

This compiles `rez-manager` and `rez-pkg-cache` (if not already built) into `build/`,
then copies `rez-pkg-cache.exe` into the `build/rez-manager.dist/` directory so that
the main executable can spawn the cache subprocess at runtime.

## Development

### Project layout

``` txt
resources/
└── icons/                # Source artwork compiled into Qt resources
src/rez_manager/
├── adapter/              # Rez API wrapper (only layer that imports rez.*)
├── data/                 # Static application data bundled with the app
├── models/               # Data models (pure Python)
├── persistence/          # Filesystem storage and project/context persistence
├── qml/                  # QML UI files
├── ui/                   # PySide6 controllers exposed to QML
└── app.py                # Application bootstrap and top-level startup wiring
docs/
├── design.md          # UI and architecture design reference
└── rez-knowledge.md   # Rez AI context / anti-hallucination guide
tests/
├── adapter/           # Adapter layer tests
├── models/            # Pure model tests
├── persistence/       # Storage and serialization tests
├── runtime/           # Runtime and exception hook tests
└── ui/                # Controller and QML-facing behavior tests
```

`adapter/` is the only layer allowed to import `rez.*`. `models/` stays pure Python, `ui/`
bridges Python and QML, and `qml/` contains the declarative interface.

See `docs/design.md` for the detailed architecture and UI specification.

### Commonly used commands

```bash
uvx ruff check src      # Lint
uvx ruff format src     # Format
uv run pytest           # Test
uv run pyside6-qml-stubgen.exe src --out-dir ./qmltypes
uv run pyside6-qmllint -I ./qmltypes <qml-files>
```

`qmltypes/` is generated output and is intentionally not tracked in git.

For correct QML hints and completion in editors such as VS Code, generate QML type stubs with
`pyside6-qml-stubgen.exe src --out-dir ./qmltypes`, then add `./qmltypes` to
`qt-qml.qmlls.additionalImportPaths`.

To lint QML files against those generated types, use
`pyside6-qmllint -I ./qmltypes <qml-files>`.

### Package caching (development)

Rez's built-in package caching spawns a `rez-pkg-cache` subprocess during context resolution.
In a production (Nuitka) build the executable is bundled alongside the main app. When running
from source you must tell Rez where to find it and enable a few package cache settings:

Create a `.env` file in the project root (already in `.gitignore`) with:

```
REZ_BIN_PATH=<path-to-rez-bin-directory>
REZ_PACKAGE_CACHE_LOCAL=1
REZ_DEFAULT_CACHABLE=1
```

- `REZ_BIN_PATH` — directory containing a pre-built `rez-pkg-cache.exe` (e.g. your Rez
  install's `Scripts/` directory).
- `REZ_PACKAGE_CACHE_LOCAL=1` — allows caching packages that live on the local filesystem
  (normally only network packages are cached).
- `REZ_DEFAULT_CACHABLE=1` — makes all packages eligible for caching (by default only
  packages that declare themselves relocatable are cached).

These environment variables are picked up automatically by the VS Code Python debugger
(which loads `.env` from the project root by default). Rez itself reads `REZ_*` prefixed
variables via its own config system — no extra library is needed.

When `REZ_BIN_PATH` is not set and the app is not frozen, `rez_bin_path` is left at its
default so package caching is disabled. Context resolution still works without caching.

## License

MIT. See `LICENSE`.
