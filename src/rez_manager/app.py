"""Application factory — creates and configures the QApplication."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

import rez_manager.rc_resources  # noqa: F401
import rez_manager.ui  # noqa: F401
from rez_manager.adapter.utils import initialize_rez
from rez_manager.logging_config import configure_logging
from rez_manager.ui.error_hub import AppErrorHub, app_error_hub


def create_app(argv: list[str]) -> tuple[QGuiApplication, QQmlApplicationEngine]:
    configure_logging()
    initialize_rez()

    import rez_manager.exception_hook  # noqa: F401

    qml_dir = Path(__file__).parent / "qml"
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE_PATH", str(qml_dir))

    app = QGuiApplication(argv)
    app.setApplicationName("rez-manager")
    app.setApplicationVersion("0.1.0")

    qmlRegisterSingletonInstance(AppErrorHub, "RezManager", 1, 0, "AppErrorHub", app_error_hub)

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.load(QUrl.fromLocalFile(str(qml_dir / "main.qml")))

    if not engine.rootObjects():
        logger.critical("Failed to load QML from {}", qml_dir / "main.qml")
        sys.exit(1)

    return app, engine
