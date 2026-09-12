"""Lightweight segmented audio level meter."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from app.ui import theme


class AudioMeter(QWidget):
    SEGMENTS = 12

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dbfs = -96.0
        self.setMinimumSize(96, 20)
        self.setMaximumHeight(20)

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        return QSize(116, 20)

    def set_level(self, dbfs: float) -> None:
        dbfs = max(-96.0, min(0.0, float(dbfs)))
        if abs(dbfs - self._dbfs) >= 0.35:
            self._dbfs = dbfs
            self.setToolTip(f"{dbfs:.1f} dBFS")
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt API)
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gap = 3
        width = max(2.0, (self.width() - gap * (self.SEGMENTS - 1)) / self.SEGMENTS)
        active = round(max(0.0, min(1.0, (self._dbfs + 60.0) / 60.0)) * self.SEGMENTS)
        inactive = QColor(theme.SURFACE_ELEVATED)
        for index in range(self.SEGMENTS):
            if index >= active:
                color = inactive
            elif index >= 10:
                color = QColor(theme.DANGER)
            elif index >= 8:
                color = QColor(theme.WARNING)
            else:
                color = QColor(theme.SUCCESS)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(int(index * (width + gap)), 5, int(width), 10, 2, 2)
