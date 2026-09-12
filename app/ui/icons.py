"""Single icon source for the BellenneRelay interface."""

from __future__ import annotations

import qtawesome as qta
from PySide6.QtGui import QIcon

from app.ui import theme


class IconProvider:
    """Create consistent Font Awesome 6 outline-style icons."""

    @staticmethod
    def _icon(name: str, color: str = theme.TEXT_SECONDARY) -> QIcon:
        return qta.icon(name, color=color)

    @classmethod
    def product(cls) -> QIcon:
        return cls._icon("fa6s.language", theme.ACCENT)

    @classmethod
    def settings(cls) -> QIcon:
        return cls._icon("fa6s.gear")

    @classmethod
    def main(cls, active: bool = False) -> QIcon:
        return cls._icon("fa6s.wave-square", theme.ACCENT if active else theme.TEXT_SECONDARY)

    @classmethod
    def overlay(cls, active: bool = False) -> QIcon:
        return cls._icon("fa6s.closed-captioning", theme.ACCENT if active else theme.TEXT_SECONDARY)

    @classmethod
    def history(cls, active: bool = False) -> QIcon:
        return cls._icon("fa6s.clock-rotate-left", theme.ACCENT if active else theme.TEXT_SECONDARY)

    @classmethod
    def logs(cls, active: bool = False) -> QIcon:
        return cls._icon("fa6s.terminal", theme.ACCENT if active else theme.TEXT_SECONDARY)

    @classmethod
    def refresh(cls) -> QIcon:
        return cls._icon("fa6s.rotate")

    @classmethod
    def play(cls) -> QIcon:
        return cls._icon("fa6s.play", "#FFFFFF")

    @classmethod
    def stop(cls) -> QIcon:
        return cls._icon("fa6s.stop", "#FFFFFF")

    @classmethod
    def close(cls) -> QIcon:
        return cls._icon("fa6s.xmark")

    @classmethod
    def eye(cls) -> QIcon:
        return cls._icon("fa6s.eye")

    @classmethod
    def pin(cls) -> QIcon:
        return cls._icon("fa6s.thumbtack")
