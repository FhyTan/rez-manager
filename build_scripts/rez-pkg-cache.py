"""Nuitka build entry point for rez-pkg-cache standalone executable."""

# nuitka-project: --mode=standalone
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --output-filename=rez-pkg-cache.exe
# nuitka-project: --include-package=rezplugins,rez
# nuitka-project: --windows-console-mode=hide
# nuitka-project: --nofollow-import-to=doctest,unittest,pytest

import os
import sys

from rez.cli._main import run
from rez.system import system

if __name__ == "__main__":
    system.rez_bin_path = os.path.dirname(sys.executable)
    run("pkg-cache")
