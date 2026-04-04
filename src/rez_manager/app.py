"""Application factory — creates and configures the QApplication."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def create_app(argv: list[str]) -> QGuiApplication:
    app = QGuiApplication(argv)
    app.setApplicationName("rez-manager")
    app.setApplicationVersion("0.1.0")

    engine = QQmlApplicationEngine()
    engine.load("qrc:/qml/main.qml")

    return app
