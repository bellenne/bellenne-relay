"""Translation-first primary page."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.icons import IconProvider
from app.ui.widgets import AudioMeter, PrimaryButton, TranscriptView


class MeterGroup(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("SectionLabel")
        self.meter = AudioMeter()
        layout.addWidget(label)
        layout.addWidget(self.meter)


class InfoGroup(QWidget):
    def __init__(self, title: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("SectionLabel")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("TechnicalValue")
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)


class MainPage(QWidget):
    overlay_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.transcript = TranscriptView(max_entries=100)
        root.addWidget(self.transcript, 1)
        root.addWidget(self._build_control_bar())
        self._compact_controls: bool | None = None

    def _build_control_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("ControlBar")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        self.control_row = QWidget()
        self.control_layout = QHBoxLayout(self.control_row)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.setSpacing(12)
        self.system_meter = MeterGroup("SYSTEM AUDIO")
        self.microphone_meter = MeterGroup("MIC")
        self.source_info = InfoGroup("SOURCE", "System Audio")
        self.language_info = InfoGroup("LANGUAGE", "English  →  Russian")
        self.latency_info = InfoGroup("LATENCY", "—")
        for widget in (
            self.system_meter,
            self.microphone_meter,
            self.source_info,
            self.language_info,
            self.latency_info,
        ):
            self.control_layout.addWidget(widget)
        self.control_layout.addStretch(1)
        self.overlay_button = QPushButton("Overlay")
        self.overlay_button.setIcon(IconProvider.overlay())
        self.overlay_button.clicked.connect(self.overlay_requested)
        self.start_stop_button = PrimaryButton()
        self.action_row = QWidget()
        self.action_layout = QHBoxLayout(self.action_row)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(8)
        self.action_layout.addStretch(1)
        self.action_layout.addWidget(self.overlay_button)
        self.action_layout.addWidget(self.start_stop_button)
        layout.addWidget(self.control_row)
        layout.addWidget(self.action_row)
        return bar

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 (Qt API)
        self._arrange_controls(event.size().width() < 980)
        super().resizeEvent(event)

    def _arrange_controls(self, compact: bool) -> None:
        if compact == self._compact_controls:
            return
        self._compact_controls = compact
        if compact:
            self.action_layout.addWidget(self.overlay_button)
            self.action_layout.addWidget(self.start_stop_button)
            self.action_row.show()
        else:
            self.control_layout.addWidget(self.overlay_button)
            self.control_layout.addWidget(self.start_stop_button)
            self.action_row.hide()

    def set_source(self, text: str) -> None:
        self.source_info.value_label.setText(text)

    def set_language(self, source_name: str, target_name: str) -> None:
        self.language_info.value_label.setText(f"{source_name}  →  {target_name}")

    def set_latency(self, latency_ms: int | None) -> None:
        self.latency_info.value_label.setText("—" if latency_ms is None else f"{latency_ms} ms")
