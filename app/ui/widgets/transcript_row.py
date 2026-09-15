"""One aligned English/Russian entry in the live transcript."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QSizePolicy, QWidget

from app.text_safety import soft_wrap_unbroken_text
from app.ui import theme


class TranscriptRow(QFrame):
    def __init__(
        self,
        timestamp: str,
        source: str,
        original: str,
        translated: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("TranscriptRow")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(5)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        meta = QLabel(f"{timestamp}   {source.title()}")
        meta.setObjectName("TranscriptMeta")
        translation_meta = QLabel(timestamp)
        translation_meta.setObjectName("TranscriptMeta")
        original_label = QLabel(soft_wrap_unbroken_text(original))
        translated_label = QLabel(soft_wrap_unbroken_text(translated))
        for label in (original_label, translated_label):
            label.setTextFormat(Qt.PlainText)
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setObjectName("TranscriptText")

        divider = QFrame()
        divider.setObjectName("TranscriptDivider")
        divider.setFixedWidth(1)
        layout.addWidget(meta, 0, 0)
        layout.addWidget(original_label, 1, 0)
        layout.addWidget(divider, 0, 1, 2, 1)
        layout.addWidget(translation_meta, 0, 2)
        layout.addWidget(translated_label, 1, 2)
        self.set_active(True)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.setStyleSheet(
            f"""
            QFrame#TranscriptRow {{
                background: {theme.ACCENT_SUBTLE if active else 'transparent'};
                border: 0;
                border-radius: 8px;
            }}
            QLabel#TranscriptMeta {{ color: {theme.TEXT_MUTED}; font-size: 11px; }}
            QLabel#TranscriptText {{ color: {theme.TEXT_PRIMARY}; font-size: 18px; }}
            QFrame#TranscriptDivider {{ background: {theme.BORDER}; border: 0; }}
            """
        )


class EmptyTranscript(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 48, 16, 48)
        title = QLabel("Your live translation will appear here")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 16px;")
        hint = QLabel("Choose an audio source, then press Start Translation")
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("MutedLabel")
        layout.addWidget(title, 0, 0)
        layout.addWidget(hint, 1, 0)
