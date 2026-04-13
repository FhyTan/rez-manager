"""Application factory — creates and configures the QApplication."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import rez_manager.exception_hook  # noqa: F401
import rez_manager.rc_resources  # noqa: F401
import rez_manager.ui  # noqa: F401


def create_app(argv: list[str]) -> tuple[QGuiApplication, QQmlApplicationEngine]:
    qml_dir = Path(__file__).parent / "qml"
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE_PATH", str(qml_dir))

    app = QGuiApplication(argv)
    app.setApplicationName("rez-manager")
    app.setApplicationVersion("0.1.0")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.load(QUrl.fromLocalFile(str(qml_dir / "main.qml")))

    if not engine.rootObjects():
        print("ERROR: Failed to load QML", file=sys.stderr)
        sys.exit(1)

    return app, engine
