"""Qt models backing the History and Logs pages."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from app.ui import theme


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    timestamp: str
    source: str
    direction: str
    original: str
    translated: str
    latency_ms: int


class HistoryModel(QAbstractTableModel):
    HEADERS = ("Time", "Source", "Direction", "Original", "Translation", "Latency")

    def __init__(self, max_entries: int = 1000) -> None:
        super().__init__()
        self.max_entries = max_entries
        self._entries: list[HistoryEntry] = []

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self._entries)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        entry = self._entries[index.row()]
        values = (
            entry.timestamp,
            entry.source.title(),
            entry.direction,
            entry.original,
            entry.translated,
            f"{entry.latency_ms} ms",
        )
        if role == Qt.DisplayRole:
            return values[index.column()]
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | (Qt.AlignRight if index.column() == 5 else Qt.AlignLeft))
        if role == Qt.ToolTipRole and index.column() in (3, 4):
            return values[index.column()]
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def add_entry(self, entry: HistoryEntry) -> None:
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._entries.insert(0, entry)
        self.endInsertRows()
        if len(self._entries) > self.max_entries:
            last = len(self._entries) - 1
            self.beginRemoveRows(QModelIndex(), last, last)
            self._entries.pop()
            self.endRemoveRows()


@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: str
    level: str
    component: str
    message: str


class LogsModel(QAbstractTableModel):
    HEADERS = ("Time", "Level", "Component", "Message")

    def __init__(self, max_entries: int = 1000) -> None:
        super().__init__()
        self.max_entries = max_entries
        self._entries: list[LogEntry] = []

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self._entries)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        entry = self._entries[index.row()]
        values = (entry.timestamp, entry.level, entry.component, entry.message)
        if role == Qt.DisplayRole:
            return values[index.column()]
        if role == Qt.ForegroundRole and index.column() == 1:
            colors = {
                "ERROR": theme.DANGER,
                "WARNING": theme.WARNING,
                "INFO": theme.SUCCESS,
                "DEBUG": theme.TEXT_MUTED,
            }
            return QColor(colors.get(entry.level, theme.TEXT_SECONDARY))
        if role == Qt.ToolTipRole:
            return entry.message
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def add_entry(self, entry: LogEntry) -> None:
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._entries.insert(0, entry)
        self.endInsertRows()
        if len(self._entries) > self.max_entries:
            last = len(self._entries) - 1
            self.beginRemoveRows(QModelIndex(), last, last)
            self._entries.pop()
            self.endRemoveRows()

    def clear(self) -> None:
        if not self._entries:
            return
        self.beginResetModel()
        self._entries.clear()
        self.endResetModel()
