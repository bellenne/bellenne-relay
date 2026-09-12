"""Always-on-top, movable and click-through subtitle overlay."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel, QSizeGrip, QVBoxLayout, QWidget

from app.config import AppSettings
from app.ui import theme


class OverlayWindow(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._drag_offset: QPoint | None = None
        self._click_through = settings.overlay_click_through
        self._editing = False
        self.setWindowTitle("BellenneRelay Overlay")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 10, 10, 6)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label, 1)
        self.grip = QSizeGrip(self)
        layout.addWidget(self.grip, 0, Qt.AlignRight | Qt.AlignBottom)
        self.resize(settings.overlay_width, settings.overlay_height)
        self.move(settings.overlay_x, settings.overlay_y)
        self.apply_style(settings.overlay_font_size, settings.overlay_opacity)
        self.set_click_through(self._click_through)

    def display(self, lines: list[str]) -> None:
        self.label.setText("\n".join(lines))
        if lines and not self.isVisible():
            self.show()

    def clear(self) -> None:
        self.label.clear()

    def apply_style(self, font_size: int, opacity: float) -> None:
        alpha = round(max(0.05, min(1.0, opacity)) * 255)
        self.setStyleSheet(
            "QWidget { background: transparent; }"
            "QLabel {"
            f" background-color: rgba(15, 20, 32, {alpha});"
            f" color: {theme.TEXT_PRIMARY}; border-radius: 8px; padding: 10px;"
            f" font-size: {font_size}px; font-weight: 600;"
            "}"
            "QSizeGrip { width: 18px; height: 18px; }"
        )

    def set_click_through(self, enabled: bool) -> None:
        self._click_through = enabled
        effective = enabled and not self._editing
        geometry = self.geometry()
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowTransparentForInput, effective)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, effective)
        self.grip.setVisible(not effective)
        self.setGeometry(geometry)
        if visible:
            self.show()

    def set_editing(self, enabled: bool) -> None:
        self._editing = enabled
        self.set_click_through(self._click_through)
        self.setWindowTitle(
            "BellenneRelay Overlay — drag/resize" if enabled else "BellenneRelay Overlay"
        )

    def place_bottom_center(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.x() + (area.width() - self.width()) // 2,
            area.bottom() - self.height() - 48,
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._editing and event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._editing and self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)
