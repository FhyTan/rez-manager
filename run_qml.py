"""QML prototype runner — launches the UI without Python backend."""

from __future__ import annotations

import os
import sys

# Use the Basic style so every button/control is unstyled and fully customizable.
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def main() -> None:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("rez-manager")
    app.setApplicationVersion("0.1.0")

    engine = QQmlApplicationEngine()
    qml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "src", "rez_manager", "qml", "main.qml",
    )
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        print("ERROR: Failed to load QML", file=sys.stderr)
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
