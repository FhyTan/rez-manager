"""Rez package cache CLI wrapper."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from rez.cli._main import run
    from rez.system import system

    if os.path.basename(sys.executable) == "rez-pkg-cache.exe":
        system.rez_bin_path = os.path.dirname(sys.executable)

    run("pkg-cache")


if __name__ == "__main__":
    main()
