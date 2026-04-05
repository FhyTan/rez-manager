"""Application factory — creates and configures the QApplication."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Must be set before QGuiApplication is created.
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def create_app(argv: list[str]) -> QGuiApplication:
    app = QGuiApplication(argv)
    app.setApplicationName("rez-manager")
    app.setApplicationVersion("0.1.0")

    qml_dir = Path(__file__).parent / "qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.load(QUrl.fromLocalFile(str(qml_dir / "main.qml")))

    if not engine.rootObjects():
        print("ERROR: Failed to load QML", file=sys.stderr)
        sys.exit(1)

    return app
