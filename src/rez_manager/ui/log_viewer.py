"""QML-facing controller for viewing the local application log file."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtQml import QmlElement

from rez_manager.persistence.app_paths import log_file_path

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1

_DEFAULT_TAIL_LINE_COUNT = 100
_TAIL_READ_BYTE_LIMIT = 64 * 1024


@QmlElement
class LogViewerController(QObject):
    stateChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._log_path = log_file_path()
        self._log_text = ""
        self._load_error = ""
        self._is_truncated = False
        self.refresh()

    @Property(str, notify=stateChanged)
    def logPath(self) -> str:  # noqa: N802
        return str(self._log_path)

    @Property(str, notify=stateChanged)
    def logUrl(self) -> str:  # noqa: N802
        return QUrl.fromLocalFile(str(self._log_path)).toString()

    @Property(str, notify=stateChanged)
    def logText(self) -> str:  # noqa: N802
        return self._log_text

    @Property(str, notify=stateChanged)
    def loadError(self) -> str:  # noqa: N802
        return self._load_error

    @Property(bool, notify=stateChanged)
    def hasContent(self) -> bool:  # noqa: N802
        return bool(self._log_text)

    @Property(bool, notify=stateChanged)
    def isTruncated(self) -> bool:  # noqa: N802
        return self._is_truncated

    @Property(int, constant=True)
    def tailLineCount(self) -> int:  # noqa: N802
        return _DEFAULT_TAIL_LINE_COUNT

    @Slot()
    def refresh(self) -> None:
        log_path = log_file_path()
        log_text = ""
        load_error = ""
        is_truncated = False

        try:
            log_text, is_truncated = _read_log_tail(log_path, _DEFAULT_TAIL_LINE_COUNT)
        except OSError as exc:
            load_error = str(exc)

        state = (log_path, log_text, load_error, is_truncated)
        if state == (self._log_path, self._log_text, self._load_error, self._is_truncated):
            return

        self._log_path, self._log_text, self._load_error, self._is_truncated = state
        self.stateChanged.emit()


def _read_log_tail(log_path: Path, tail_line_count: int) -> tuple[str, bool]:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file does not exist: {log_path}")

    with log_path.open("rb") as stream:
        stream.seek(0, 2)
        file_size = stream.tell()
        read_size = min(file_size, _TAIL_READ_BYTE_LIMIT)
        stream.seek(max(0, file_size - read_size))
        raw_bytes = stream.read(read_size)

    decoded_text = raw_bytes.decode("utf-8", errors="replace")
    lines = decoded_text.splitlines()
    if file_size > read_size and lines:
        lines = lines[1:]

    is_truncated = file_size > read_size or len(lines) > tail_line_count
    tail_lines = lines[-tail_line_count:]
    return "\n".join(tail_lines), is_truncated
