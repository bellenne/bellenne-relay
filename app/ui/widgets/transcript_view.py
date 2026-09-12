"""Continuous, aligned bilingual conversation feed."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.transcript_row import EmptyTranscript, TranscriptRow


class TranscriptView(QWidget):
    def __init__(self, max_entries: int = 100, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.max_entries = max_entries
        self._rows: list[TranscriptRow] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.feed = QWidget()
        self.feed_layout = QVBoxLayout(self.feed)
        self.feed_layout.setContentsMargins(8, 8, 8, 8)
        self.feed_layout.setSpacing(4)
        self.empty_state = EmptyTranscript()
        self.feed_layout.addWidget(self.empty_state)
        self.feed_layout.addStretch(1)
        self.scroll.setWidget(self.feed)
        root.addWidget(self.scroll, 1)

        state = QFrame()
        state.setObjectName("TranscriptState")
        state_layout = QHBoxLayout(state)
        state_layout.setContentsMargins(16, 8, 16, 8)
        self.state_label = QLabel("Ready to translate")
        self.state_label.setObjectName("MutedLabel")
        state_layout.addWidget(self.state_label)
        state_layout.addStretch()
        root.addWidget(state)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("TranscriptHeader")
        layout = QGridLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setHorizontalSpacing(16)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedWidth(1)
        source_header, self.source_code, self.source_name = self._language_header(
            "EN", "English", "Original"
        )
        target_header, self.target_code, self.target_name = self._language_header(
            "RU", "Russian", "Translation"
        )
        layout.addLayout(source_header, 0, 0)
        layout.addWidget(divider, 0, 1)
        layout.addLayout(target_header, 0, 2)
        return header

    @staticmethod
    def _language_header(code: str, language: str, role: str) -> tuple[QHBoxLayout, QLabel, QLabel]:
        layout = QHBoxLayout()
        layout.setSpacing(10)
        code_label = QLabel(code)
        code_label.setObjectName("LanguageCode")
        code_label.setFixedSize(34, 26)
        code_label.setAlignment(Qt.AlignCenter)
        text = QVBoxLayout()
        text.setSpacing(1)
        language_label = QLabel(language)
        language_label.setObjectName("LanguageName")
        role_label = QLabel(role)
        role_label.setObjectName("MutedLabel")
        text.addWidget(language_label)
        text.addWidget(role_label)
        layout.addWidget(code_label)
        layout.addLayout(text)
        layout.addStretch()
        return layout, code_label, language_label

    def add_entry(self, timestamp: str, source: str, original: str, translated: str) -> None:
        if self.empty_state.isVisible():
            self.empty_state.hide()
        if self._rows:
            self._rows[-1].set_active(False)
        row = TranscriptRow(timestamp, source, original, translated)
        self._rows.append(row)
        self.feed_layout.insertWidget(self.feed_layout.count() - 1, row)
        while len(self._rows) > self.max_entries:
            old = self._rows.pop(0)
            self.feed_layout.removeWidget(old)
            old.deleteLater()
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def set_speech_state(self, text: str) -> None:
        self.state_label.setText(text)

    def set_languages(
        self,
        source_code: str,
        source_name: str,
        target_code: str,
        target_name: str,
    ) -> None:
        self.source_code.setText(source_code.upper())
        self.source_name.setText(source_name)
        self.target_code.setText(target_code.upper())
        self.target_name.setText(target_name)

    def clear(self) -> None:
        for row in self._rows:
            self.feed_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self.empty_state.show()
