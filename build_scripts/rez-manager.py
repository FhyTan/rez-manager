"""Nuitka build entry point for rez-manager."""

# nuitka-project: --mode=standalone
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --enable-plugins=pyside6
# nuitka-project: --include-qt-plugins=qml
# nuitka-project: --include-package=rezplugins
# nuitka-project: --user-package-configuration-file=./build_scripts/nuitka-package.config.yml
# nuitka-project: --output-filename=rez-manager.exe
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --windows-icon-from-ico=./resources/icons/logo/rez_manager.ico
# nuitka-project: --nofollow-import-to=doctest,unittest,pytest
# nuitka-project: --noinclude-dlls=qt63d*.dll
# nuitka-project: --noinclude-dlls=qt6quick3d*.dll
# nuitka-project: --noinclude-dlls=qt6webengine*.dll

from rez_manager.__main__ import main

if __name__ == "__main__":
    main()
