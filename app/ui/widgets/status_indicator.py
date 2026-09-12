"""Compact semantic status indicator."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from app.ui import theme


class StatusIndicator(QWidget):
    def __init__(self, text: str = "Ready", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self._color = QColor(theme.SUCCESS)
        self.setMinimumHeight(28)

    def set_status(self, text: str, color: str) -> None:
        self._text = text
        self._color = QColor(color)
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        width = QFontMetrics(self.font()).horizontalAdvance(self._text) + 30
        return QSize(width, 28)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt API)
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(3, (self.height() - 8) // 2, 8, 8)
        painter.setPen(QColor(theme.TEXT_SECONDARY))
        painter.drawText(19, 0, self.width() - 19, self.height(), Qt.AlignVCenter, self._text)
