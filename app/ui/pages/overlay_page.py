"""Overlay preview and controls."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.text_safety import soft_wrap_unbroken_text
from app.ui import theme
from app.ui.icons import IconProvider


class OverlayPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        title = QLabel("Overlay")
        title.setObjectName("PanelTitle")
        subtitle = QLabel("Preview and control the always-on-top subtitle window")
        subtitle.setObjectName("MutedLabel")
        root.addWidget(title)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(20)
        preview = QFrame()
        preview.setObjectName("OverlayPreview")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(32, 32, 32, 32)
        preview_layout.addStretch()
        self.preview_original = QLabel("Language shouldn't be a barrier to great ideas.")
        self.preview_original.setAlignment(Qt.AlignCenter)
        self.preview_original.setTextFormat(Qt.PlainText)
        self.preview_original.setWordWrap(True)
        self.preview_original.setMinimumWidth(0)
        self.preview_original.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.preview_original.setObjectName("OverlayOriginal")
        self.preview_translation = QLabel("Язык не должен быть преградой для великих идей.")
        self.preview_translation.setAlignment(Qt.AlignCenter)
        self.preview_translation.setTextFormat(Qt.PlainText)
        self.preview_translation.setWordWrap(True)
        self.preview_translation.setMinimumWidth(0)
        self.preview_translation.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.preview_translation.setObjectName("OverlayTranslation")
        preview_layout.addWidget(self.preview_original)
        preview_layout.addWidget(self.preview_translation)
        preview_layout.addStretch()
        content.addWidget(preview, 1)

        controls = QFrame()
        controls.setObjectName("Panel")
        controls.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(16)
        controls_title = QLabel("Overlay settings")
        controls_title.setObjectName("PanelTitle")
        controls_layout.addWidget(controls_title)
        form = QFormLayout()
        form.setSpacing(12)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(12, 64)
        self.font_spin.setSuffix(" px")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.lines_spin = QSpinBox()
        self.lines_spin.setRange(1, 8)
        form.addRow("Font size", self.font_spin)
        form.addRow("Opacity", self.opacity_slider)
        form.addRow("Entries", self.lines_spin)
        controls_layout.addLayout(form)
        self.original_check = QCheckBox("Show original English")
        self.click_check = QCheckBox("Mouse click-through")
        controls_layout.addWidget(self.original_check)
        controls_layout.addWidget(self.click_check)
        controls_layout.addStretch()
        self.show_button = QPushButton("Show / Hide Overlay")
        self.show_button.setIcon(IconProvider.eye())
        self.edit_button = QPushButton("Edit position")
        self.edit_button.setIcon(IconProvider.pin())
        self.edit_button.setCheckable(True)
        self.reset_button = QPushButton("Move to bottom center")
        controls_layout.addWidget(self.show_button)
        controls_layout.addWidget(self.edit_button)
        controls_layout.addWidget(self.reset_button)
        content.addWidget(controls)
        root.addLayout(content, 1)

    def update_preview(self, original: str, translated: str) -> None:
        self.preview_original.setText(soft_wrap_unbroken_text(original))
        self.preview_translation.setText(soft_wrap_unbroken_text(translated))

    def set_languages(self, source_name: str, target_name: str) -> None:
        self.original_check.setText(f"Show original {source_name}")
        examples = {
            ("English", "Russian"): (
                "Language shouldn't be a barrier to great ideas.",
                "Язык не должен быть преградой для великих идей.",
            ),
            ("Russian", "English"): (
                "Язык не должен быть преградой для великих идей.",
                "Language shouldn't be a barrier to great ideas.",
            ),
        }
        original, translated = examples[(source_name, target_name)]
        self.update_preview(original, translated)

    def apply_preview_options(self, font_size: int, opacity: float, show_original: bool) -> None:
        alpha = round(max(0.1, min(1.0, opacity)) * 255)
        self.preview_original.setVisible(show_original)
        self.preview_translation.setStyleSheet(
            f"background: rgba(15, 20, 32, {alpha}); color: {theme.TEXT_PRIMARY}; "
            f"font-size: {font_size}px; padding: 12px; border-radius: 8px;"
        )
        self.preview_original.setStyleSheet(
            f"background: rgba(15, 20, 32, {alpha}); color: {theme.TEXT_SECONDARY}; "
            f"font-size: {max(12, font_size - 4)}px; padding: 8px; border-radius: 8px;"
        )
