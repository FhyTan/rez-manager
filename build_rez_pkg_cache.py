"""Nuitka build entry point for rez-pkg-cache standalone executable.

Built alongside the main rez-manager.exe so that Rez's package caching
subprocess (``rez-pkg-cache --daemon``) can be found on PATH at runtime.
"""

# nuitka-project: --mode=standalone
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --include-package=rezplugins
# nuitka-project: --user-package-configuration-file=./nuitka-package.config.yml
# nuitka-project: --output-filename=rez-pkg-cache.exe

from rez_manager.rez_pkg_cache import main

main()
