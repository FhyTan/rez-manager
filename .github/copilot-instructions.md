# GitHub Copilot Instructions — rez-manager

## Project Overview

`rez-manager` is a **PySide6 + QML** desktop GUI for managing [Rez](https://rez.readthedocs.io/en/stable/) package environments.
It allows users to create, configure, and launch Rez contexts (resolved environments) per project
through a visual interface, without using the command line.

**Package manager:** `uv` — always use `uv add`, `uv run`, `uvx` instead of `pip` / `python` directly.
**Linter/formatter:** `ruff` — run via `uvx ruff check src` and `uvx ruff format src`.
**Test runner:** `pytest` — run via `uv run pytest`.

---

## Knowledge Base References

Before writing any Rez-related code, consult:

- **`docs/rez-knowledge.md`** — Anti-hallucination guide for Rez: core concepts, safe Python patterns, common failure modes, official links.
- **`docs/design.md`** — Full UI and architecture design reference: window layouts, data models, on-disk file schema, layer rules.

---

## Architecture

```
src/rez_manager/
├── adapter/        # ONLY layer that imports from rez.*
├── models/         # Pure Python dataclasses — NO rez.* or PySide6 imports
├── persistence/    # Filesystem persistence helpers
├── ui/             # PySide6 QObject subclasses (controllers); exposed to QML via @Property/@Slot/Signal
└── qml/            # Declarative QML UI — communicates with ui/ only
```

### Layer Rules (strictly enforced)

1. `adapter/` is the **only** module that imports `rez.*`.
2. `models/` has **no** imports from `rez.*` or `PySide6`.
3. `ui/` imports `models/` and `adapter/`; exposes `@Property`, `@Slot`, `Signal` to QML.
4. `qml/` only communicates with `ui/` through registered QML types and signals.

---

## Code Conventions

- **Language:** All source code, comments, docstrings, and identifiers must be in **English**.
- UI display strings are kept separate for i18n (do not hardcode translated text in logic).
- Line length: **100 characters** (enforced by ruff).
- Use `from __future__ import annotations` for forward references.
- Use `loguru` as the default logging library; avoid ad-hoc `print()` debugging and only use the standard `logging` module when integration requires it.
- Use `platformdirs` to determine application config, data, cache, and log directories; do not hardcode OS-specific storage paths.
- Prefer dataclasses or Pydantic models in `models/`; avoid mixing data with logic.
- Keep `adapter/` thin — one module per concern (`context.py`, `packages.py`).
- Never assume a Rez call succeeds — always check return codes and handle errors.

### Logging and App Paths

- Centralize logger setup so log sinks, formatting, and rotation are configured in one place.
- Write runtime logs to an application log directory resolved via `platformdirs`.
- Store user configuration, persistent app data, cache data, and logs in their respective `platformdirs` locations rather than alongside source files.
- Use `pathlib.Path` together with `platformdirs` results when composing filesystem paths.

---

## PySide6 / QML Patterns

See `.github/instructions/qml-python.instructions.md` for full details.

---

## Rez Integration Patterns

See `docs/rez-knowledge.md` for full details. Summary:

```python
# Preferred: in-process resolve (keep in adapter/ only)
from rez.resolved_context import ResolvedContext
ctx = ResolvedContext(["maya-2024", "python-3.11"])
```

- **Never** import `rez.*` outside of `src/rez_manager/adapter/`.
- **Never** invent Rez API methods — verify against https://rez.readthedocs.io/en/stable/api.html
- Rez package request strings always use `-` to separate package name and version. If a source package family
  name contains `-`, Rez normalizes it before it enters the Rez API, so downstream code should not add extra
  defensive parsing for labels like `my-tool`; treat the final `-` as the package/version separator.

---

## On-Disk Context Format

```
<contexts_location>/<project>/<context>/
├── context.rxt    # Rez serialized context
├── meta.json      # { name, description, launch_target, custom_command, packages }
└── thumbnail.png
```

---

## Common Commands

```bash
uv sync                    # Install dependencies
uv run rez-manager         # Launch the app
uv run pytest              # Run tests
uvx ruff check src         # Lint
uvx ruff format src        # Format
pyside6-qml-stubgen.exe src --out-dir ./qmltypes
pyside6-qmllint -I ./qmltypes <qml-files>
pyside6-qmlformat -i <qml-files>
```

## Development

The project is still in the development phase, so there’s no need for backward compatibility. Feel free to make any structural changes if they improve the design.
