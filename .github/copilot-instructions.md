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
- Prefer dataclasses or Pydantic models in `models/`; avoid mixing data with logic.
- Keep `adapter/` thin — one module per concern (`context.py`, `packages.py`).
- Never assume a Rez call succeeds — always check return codes and handle errors.

---

## PySide6 / QML Patterns

- Register Python types with `qmlRegisterType` or `@QmlElement` decorator.
- Use `Signal` for QML notifications, `@Property` for bindable values, `@Slot` for callable actions.
- QML files live in `src/rez_manager/qml/`; load via Qt resource system or `QUrl.fromLocalFile`.
- Prefer `ListView` + delegate pattern for all list/card UIs.

---

## Rez Integration Patterns

See `docs/rez-knowledge.md` for full details. Summary:

```python
# Preferred: in-process resolve (keep in adapter/ only)
from rez.resolved_context import ResolvedContext
ctx = ResolvedContext(["maya-2024", "python-3.11"])

# Fallback: subprocess for CLI commands
import subprocess
proc = subprocess.run(["rez-env", ...], capture_output=True, text=True, check=False)
```

- **Never** import `rez.*` outside of `src/rez_manager/adapter/`.
- **Never** invent Rez API methods — verify against https://rez.readthedocs.io/en/stable/api.html

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
```
