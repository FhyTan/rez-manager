"""QML-facing list model for launch target options."""

from __future__ import annotations

from PySide6.QtCore import Property, QAbstractListModel, QByteArray, QModelIndex, Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

from rez_manager.models.launch_target import LAUNCH_TARGETS, LaunchTarget, LaunchTargetDefinition

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class LaunchTargetListModel(QAbstractListModel):
    """Expose supported launch targets and their metadata to QML."""

    ValueRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2
    AccentColorRole = Qt.ItemDataRole.UserRole + 3
    IconNameRole = Qt.ItemDataRole.UserRole + 4
    IconSourceRole = Qt.ItemDataRole.UserRole + 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items = list(LAUNCH_TARGETS.all())

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.ValueRole: QByteArray(b"value"),
            self.LabelRole: QByteArray(b"label"),
            self.AccentColorRole: QByteArray(b"accentColor"),
            self.IconNameRole: QByteArray(b"iconName"),
            self.IconSourceRole: QByteArray(b"iconSource"),
        }

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: ANN201
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._items):
            return None

        target = self._items[index.row()]
        if role == self.ValueRole:
            return target.value.value
        if role == self.LabelRole:
            return target.label
        if role == self.AccentColorRole:
            return QColor(target.color)
        if role == self.IconNameRole:
            return target.icon_name
        if role == self.IconSourceRole:
            return target.icon_source
        return None

    @Property(str, constant=True)
    def defaultValue(self) -> str:  # noqa: N802
        return LaunchTarget.SHELL.value

    @Property(str, constant=True)
    def customValue(self) -> str:  # noqa: N802
        return LaunchTarget.CUSTOM.value

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict[str, object]:
        if index < 0 or index >= len(self._items):
            return {}
        return _target_payload(self._items[index])

    @Slot(str, result="QVariantMap")
    def option(self, value: str) -> dict[str, object]:
        try:
            target = LAUNCH_TARGETS.from_value(value)
        except (TypeError, ValueError):
            return {}
        return _target_payload(target)


def _target_payload(target: LaunchTargetDefinition) -> dict[str, object]:
    return {
        "value": target.value.value,
        "label": target.label,
        "accentColor": target.color,
        "iconName": target.icon_name,
        "iconSource": target.icon_source,
    }
