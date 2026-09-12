"""Structured technical log page."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.ui.models import LogEntry, LogsModel


class LogsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        heading = QHBoxLayout()
        text = QVBoxLayout()
        title = QLabel("Logs")
        title.setObjectName("PanelTitle")
        subtitle = QLabel("Audio, speech recognition, and translation diagnostics")
        subtitle.setObjectName("MutedLabel")
        text.addWidget(title)
        text.addWidget(subtitle)
        clear_button = QPushButton("Clear")
        heading.addLayout(text)
        heading.addStretch()
        heading.addWidget(clear_button)
        root.addLayout(heading)

        self.model = LogsModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(38)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        clear_button.clicked.connect(self.model.clear)
        root.addWidget(self.table, 1)

    def add_entry(self, entry: LogEntry) -> None:
        self.model.add_entry(entry)
