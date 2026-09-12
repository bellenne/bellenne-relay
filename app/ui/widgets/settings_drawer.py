"""Animated settings drawer for the secondary runtime controls."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.languages import SUPPORTED_LANGUAGE_PAIRS
from app.ui.icons import IconProvider


class SettingsDrawer(QFrame):
    close_requested = Signal()
    refresh_requested = Signal()

    WIDTH = 328

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsDrawer")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)
        self._open = False
        self._animation = QPropertyAnimation(self, b"maximumWidth", self)
        self._animation.setDuration(190)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.finished.connect(self._animation_finished)
        self._build_ui()

    @property
    def is_open(self) -> bool:
        return self._open

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        heading = QHBoxLayout()
        title = QLabel("Settings")
        title.setObjectName("PanelTitle")
        close_button = QToolButton()
        close_button.setIcon(IconProvider.close())
        close_button.setToolTip("Close settings")
        close_button.clicked.connect(self.close_requested)
        heading.addWidget(title)
        heading.addStretch()
        heading.addWidget(close_button)
        root.addLayout(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 4, 0)
        content_layout.setSpacing(16)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        audio_title = QLabel("AUDIO")
        audio_title.setObjectName("SectionLabel")
        content_layout.addWidget(audio_title)
        self.audio_form = QFormLayout()
        self.audio_form.setSpacing(12)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("System Audio", "system")
        self.mode_combo.addItem("Microphone", "microphone")
        self.mode_combo.addItem("System + Microphone", "both")
        self.system_combo = QComboBox()
        self.microphone_combo = QComboBox()
        self.audio_form.addRow("Source", self.mode_combo)
        self.audio_form.addRow("Output", self.system_combo)
        self.audio_form.addRow("Microphone", self.microphone_combo)
        content_layout.addLayout(self.audio_form)

        self.headphone_warning = QLabel(
            "Use headphones with System + Microphone to reduce acoustic echo."
        )
        self.headphone_warning.setObjectName("MutedLabel")
        self.headphone_warning.setWordWrap(True)
        content_layout.addWidget(self.headphone_warning)

        refresh_button = QPushButton("Refresh devices")
        refresh_button.setIcon(IconProvider.refresh())
        refresh_button.clicked.connect(self.refresh_requested)
        self.refresh_button = refresh_button
        content_layout.addWidget(refresh_button)

        language_title = QLabel("TRANSLATION")
        language_title.setObjectName("SectionLabel")
        content_layout.addWidget(language_title)
        language_form = QFormLayout()
        language_form.setSpacing(12)
        self.language_combo = QComboBox()
        for pair in SUPPORTED_LANGUAGE_PAIRS:
            self.language_combo.addItem(pair.label, pair.key)
        self.language_filter_check = QCheckBox("Ignore other languages")
        self.language_filter_check.setToolTip(
            "Discard speech confidently detected as a language other than the selected input"
        )
        language_form.addRow("Direction", self.language_combo)
        language_form.addRow("Input filter", self.language_filter_check)
        content_layout.addLayout(language_form)

        model_title = QLabel("PROCESSING")
        model_title.setObjectName("SectionLabel")
        content_layout.addWidget(model_title)
        model_form = QFormLayout()
        model_form.setSpacing(12)
        self.model_combo = QComboBox()
        self.model_combo.addItem("Turbo (recommended)", "turbo")
        for model in ("tiny", "base", "small", "medium"):
            self.model_combo.addItem(model.title(), model)
        self.compute_combo = QComboBox()
        self.compute_combo.addItem("Auto", "auto")
        self.compute_combo.addItem("CPU", "cpu")
        self.compute_combo.addItem("CUDA", "cuda")
        model_form.addRow("Whisper", self.model_combo)
        model_form.addRow("Compute", self.compute_combo)
        content_layout.addLayout(model_form)

        status_title = QLabel("SERVICES")
        status_title.setObjectName("SectionLabel")
        content_layout.addWidget(status_title)
        self.component_labels: dict[str, QLabel] = {}
        for component, label in (
            ("system", "System audio"),
            ("microphone", "Microphone"),
            ("whisper", "Whisper"),
            ("translator", "Translator"),
        ):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addStretch()
            value = QLabel("Stopped")
            value.setObjectName("TechnicalValue")
            self.component_labels[component] = value
            row.addWidget(value)
            content_layout.addLayout(row)
        content_layout.addStretch()

    def set_open(self, opened: bool) -> None:
        self._open = opened
        self.setVisible(True)
        self._animation.stop()
        self._animation.setStartValue(self.maximumWidth())
        self._animation.setEndValue(self.WIDTH if opened else 0)
        self._animation.start()

    def toggle(self) -> None:
        self.set_open(not self._open)

    def set_component_status(self, component: str, status: str) -> None:
        if label := self.component_labels.get(component):
            label.setText(status.title())

    def set_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self.mode_combo,
            self.system_combo,
            self.microphone_combo,
            self.language_combo,
            self.language_filter_check,
            self.model_combo,
            self.compute_combo,
            self.refresh_button,
        ):
            widget.setEnabled(enabled)

    def update_source_visibility(self) -> None:
        mode = self.mode_combo.currentData()
        self.audio_form.setRowVisible(self.system_combo, mode in ("system", "both"))
        self.audio_form.setRowVisible(
            self.microphone_combo, mode in ("microphone", "both")
        )
        self.headphone_warning.setVisible(mode == "both")

    def _animation_finished(self) -> None:
        if not self._open:
            self.setVisible(False)
