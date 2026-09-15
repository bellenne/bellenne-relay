"""Continuous, aligned bilingual conversation feed."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
        self._follow_latest = True
        self._auto_scrolling = False
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
        self.scroll.verticalScrollBar().valueChanged.connect(self._scroll_position_changed)
        root.addWidget(self.scroll, 1)

        state = QFrame()
        state.setObjectName("TranscriptState")
        state_layout = QHBoxLayout(state)
        state_layout.setContentsMargins(16, 8, 16, 8)
        self.state_label = QLabel("Ready to translate")
        self.state_label.setObjectName("MutedLabel")
        state_layout.addWidget(self.state_label)
        state_layout.addStretch()
        self.latest_button = QPushButton("↓ Latest")
        self.latest_button.setToolTip("Return to the newest translation")
        self.latest_button.clicked.connect(self.follow_latest)
        self.latest_button.hide()
        state_layout.addWidget(self.latest_button)
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
        was_following_latest = self._follow_latest
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
        if was_following_latest:
            QTimer.singleShot(0, lambda current=row: self._scroll_to_entry(current, resume=True))
        else:
            self.latest_button.show()

    def follow_latest(self) -> None:
        self._follow_latest = True
        self.latest_button.hide()
        if self._rows:
            QTimer.singleShot(0, lambda: self._scroll_to_entry(self._rows[-1], resume=True))

    def _scroll_position_changed(self, value: int) -> None:
        if self._auto_scrolling:
            return
        bar = self.scroll.verticalScrollBar()
        self._follow_latest = value >= bar.maximum() - 2
        self.latest_button.setVisible(bool(self._rows) and not self._follow_latest)

    def _scroll_to_entry(self, row: TranscriptRow, *, resume: bool = False) -> None:
        if resume:
            self._follow_latest = True
        if not self._follow_latest or row not in self._rows:
            return
        self.feed_layout.activate()
        bar = self.scroll.verticalScrollBar()
        target = latest_row_scroll_value(
            row_top=row.y(),
            row_height=row.height(),
            viewport_height=self.scroll.viewport().height(),
            maximum=bar.maximum(),
        )
        self._auto_scrolling = True
        try:
            bar.setValue(target)
        finally:
            self._auto_scrolling = False
        self.latest_button.hide()

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
        self._follow_latest = True
        self.latest_button.hide()
        self.empty_state.show()
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(0))


def latest_row_scroll_value(
    *,
    row_top: int,
    row_height: int,
    viewport_height: int,
    maximum: int,
    margin: int = 8,
) -> int:
    """Keep the latest row visible without blindly jumping to the feed bottom."""
    if row_height + margin * 2 >= viewport_height:
        desired = row_top - margin
    else:
        desired = row_top + row_height + margin - viewport_height
    return min(maximum, max(0, desired))
