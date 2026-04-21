# rez-manager

***This app is in early development and not yet ready for production use.!***

A GUI tool for managing [Rez](https://rez.readthedocs.io/en/stable/) package environments.

![MainWindow](./images/MainWindow.png)

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run rez-manager
```

## Development

```bash
uvx ruff check src      # Lint
uvx ruff format src     # Format
uv run pytest           # Test
```

For correct QML hints and completion in editors such as VS Code, add `./qmltypes` to
`qt-qml.qmlls.additionalImportPaths`.

## Project Layout

```
src/rez_manager/
├── adapter/    # Rez API wrapper (only layer that imports rez.*)
├── models/     # Data models (pure Python)
├── ui/         # PySide6 controllers exposed to QML
└── qml/        # QML UI files
docs/
├── design.md          # UI and architecture design reference
└── rez-knowledge.md   # Rez AI context / anti-hallucination guide
```

See `docs/design.md` for full architecture and UI specification.

## License

MIT. See `LICENSE`.
