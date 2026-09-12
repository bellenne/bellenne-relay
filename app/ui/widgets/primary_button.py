"""Start/stop button with semantic state styling."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QWidget

from app.ui.icons import IconProvider


class PrimaryButton(QPushButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Start Translation", parent)
        self.setObjectName("PrimaryButton")
        self.setIcon(IconProvider.play())
        self.setMinimumWidth(164)

    def set_running(self, running: bool) -> None:
        self.setText("Stop Translation" if running else "Start Translation")
        self.setIcon(IconProvider.stop() if running else IconProvider.play())
        self.setObjectName("StopButton" if running else "PrimaryButton")
        self.style().unpolish(self)
        self.style().polish(self)
