"""Replaceable subtitle destination contract."""

from __future__ import annotations

from typing import Protocol


class SubtitleOutput(Protocol):
    def display(self, lines: list[str]) -> None:
        """Display the current subtitle lines."""

    def clear(self) -> None:
        """Clear displayed subtitles."""
