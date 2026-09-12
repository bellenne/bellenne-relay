"""Central BellenneRelay design tokens and application stylesheet."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

BG = "#0F1420"
SURFACE = "#1A2233"
SURFACE_ELEVATED = "#2A3346"
SURFACE_HOVER = "#333E53"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#AAB3C2"
TEXT_MUTED = "#6B7587"
BORDER = "rgba(255, 255, 255, 0.08)"
STRONG_BORDER = "rgba(255, 255, 255, 0.12)"
ACCENT = "#FF7A59"
ACCENT_HOVER = "#FF8F73"
ACCENT_ACTIVE = "#E86445"
ACCENT_SUBTLE = "rgba(255, 122, 89, 0.10)"
ACCENT_SELECTED = "rgba(255, 122, 89, 0.16)"
SUCCESS = "#22D3A5"
WARNING = "#F59E0B"
DANGER = "#FF5C70"
INFORMATION = "#A855F7"

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 20, "2xl": 24, "3xl": 32}
RADIUS = {"small": 6, "control": 8, "button": 9, "panel": 12}


def preferred_font_family() -> str:
    """Return Inter when installed, otherwise the native Windows UI font."""
    families = {family.casefold(): family for family in QFontDatabase.families()}
    return families.get("inter", "Segoe UI")


def _register_windows_fonts() -> None:
    """Make UI fonts available to Qt even with minimal/headless platform plugins."""
    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    fonts_dir = windows_dir / "Fonts"
    if not fonts_dir.is_dir():
        return
    candidates = [*fonts_dir.glob("Inter*.ttf"), *fonts_dir.glob("segoeui*.ttf")]
    for path in candidates:
        QFontDatabase.addApplicationFont(str(path))


def apply_theme(application: QApplication) -> None:
    """Apply the BellenneRelay palette, typography, and shared component rules."""
    _register_windows_fonts()
    family = preferred_font_family()
    application.setFont(QFont(family, 10))
    application.setStyleSheet(
        f"""
        * {{
            font-family: "{family}";
        }}
        QMainWindow, QDialog, QWidget#AppRoot {{
            background: {BG};
            color: {TEXT_PRIMARY};
        }}
        QWidget {{
            color: {TEXT_PRIMARY};
            font-size: 13px;
        }}
        QLabel#ProductName {{ font-size: 20px; font-weight: 600; }}
        QLabel#ProductSubtitle, QLabel#MutedLabel {{ color: {TEXT_MUTED}; font-size: 12px; }}
        QLabel#PanelTitle {{ font-size: 16px; font-weight: 600; }}
        QLabel#SectionLabel {{ color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 600; }}
        QLabel#TechnicalValue {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
        QLabel#LanguageCode {{
            color: {ACCENT}; background: {ACCENT_SUBTLE}; border-radius: 6px;
            font-size: 12px; font-weight: 600;
        }}
        QLabel#LanguageName {{ color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 600; }}
        QFrame#Header, QFrame#Navigation, QFrame#ControlBar {{
            background: {SURFACE};
            border: 0;
        }}
        QFrame#Header {{ border-bottom: 1px solid {BORDER}; }}
        QFrame#Navigation {{ border-bottom: 1px solid {BORDER}; }}
        QFrame#ControlBar {{ border-top: 1px solid {BORDER}; }}
        QFrame#Panel, QWidget#Panel {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
        }}
        QFrame#Divider {{ background: {BORDER}; border: 0; }}
        QFrame#TranscriptHeader {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}
        QFrame#TranscriptState {{ background: {BG}; border-top: 1px solid {BORDER}; }}
        QFrame#SettingsDrawer {{
            background: {SURFACE}; border-left: 1px solid {STRONG_BORDER}; border-radius: 0;
        }}
        QFrame#OverlayPreview {{
            background: {SURFACE_ELEVATED}; border: 1px solid {BORDER}; border-radius: 12px;
        }}
        QPushButton, QToolButton {{
            background: {SURFACE_ELEVATED};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
            min-height: 36px;
            padding: 0 12px;
        }}
        QPushButton:hover, QToolButton:hover {{ background: {SURFACE_HOVER}; }}
        QPushButton:pressed, QToolButton:pressed {{ background: {BG}; }}
        QPushButton:disabled, QToolButton:disabled {{ color: {TEXT_MUTED}; background: {SURFACE}; }}
        QPushButton#PrimaryButton {{
            background: {ACCENT}; color: #FFFFFF; border: 0; border-radius: 9px;
            min-height: 44px; padding: 0 20px; font-weight: 600;
        }}
        QPushButton#PrimaryButton:hover {{ background: {ACCENT_HOVER}; }}
        QPushButton#PrimaryButton:pressed {{ background: {ACCENT_ACTIVE}; }}
        QPushButton#StopButton {{
            background: {DANGER}; color: #FFFFFF; border: 0; border-radius: 9px;
            min-height: 44px; padding: 0 20px; font-weight: 600;
        }}
        QPushButton#NavButton {{
            color: {TEXT_SECONDARY}; background: transparent; border: 0;
            border-radius: 0; min-height: 42px; padding: 0 12px;
        }}
        QPushButton#NavButton:hover {{ color: {TEXT_PRIMARY}; background: transparent; }}
        QPushButton#NavButton[active="true"] {{
            color: {ACCENT}; border-bottom: 2px solid {ACCENT};
        }}
        QComboBox, QSpinBox {{
            background: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};
            border-radius: 8px; min-height: 36px; padding: 0 10px;
        }}
        QComboBox:hover, QSpinBox:hover {{ background: {SURFACE_HOVER}; }}
        QComboBox:focus, QSpinBox:focus {{ border: 1px solid {ACCENT}; }}
        QComboBox::drop-down {{ border: 0; width: 28px; }}
        QComboBox QAbstractItemView {{
            background: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY};
            border: 1px solid {STRONG_BORDER};
            selection-background-color: {ACCENT_SELECTED}; outline: 0; padding: 4px;
        }}
        QCheckBox {{ color: {TEXT_SECONDARY}; spacing: 8px; }}
        QCheckBox::indicator {{
            width: 16px; height: 16px; border: 1px solid {STRONG_BORDER};
            border-radius: 4px; background: {SURFACE_ELEVATED};
        }}
        QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
        QSlider::groove:horizontal {{
            height: 4px; background: {SURFACE_ELEVATED}; border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
        QSlider::handle:horizontal {{
            width: 14px; margin: -5px 0; background: {TEXT_PRIMARY}; border-radius: 7px;
        }}
        QProgressBar {{
            background: {SURFACE_ELEVATED}; border: 0; border-radius: 4px;
            min-height: 8px; max-height: 8px;
        }}
        QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
        QLabel#SetupError {{ color: {DANGER}; font-size: 12px; }}
        QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: 0; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
        QScrollBar::handle:vertical {{
            background: {SURFACE_ELEVATED}; border-radius: 4px; min-height: 28px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QTableView {{
            background: {BG}; alternate-background-color: {BG}; color: {TEXT_PRIMARY};
            border: 0; gridline-color: {BORDER}; selection-background-color: {ACCENT_SELECTED};
            selection-color: {TEXT_PRIMARY}; outline: 0;
        }}
        QTableView::item {{ border-bottom: 1px solid {BORDER}; padding: 8px; }}
        QTableView::item:hover {{ background: rgba(255, 255, 255, 0.03); }}
        QHeaderView::section {{
            background: {SURFACE}; color: {TEXT_SECONDARY}; border: 0;
            border-bottom: 1px solid {STRONG_BORDER}; padding: 8px; font-weight: 600;
        }}
        QToolTip {{
            background: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY};
            border: 1px solid {STRONG_BORDER};
        }}
        """
    )
