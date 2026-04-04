"""Entry point for the rez-manager application."""

from __future__ import annotations

import sys

from rez_manager.app import create_app


def main() -> None:
    app = create_app(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
