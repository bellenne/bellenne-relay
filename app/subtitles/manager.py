"""Format translated results and maintain a short overlay history."""

from __future__ import annotations

from collections import deque

from app.translation import TranslationResult

from .deduplicator import SubtitleDeduplicator
from .output import SubtitleOutput


class SubtitleManager:
    def __init__(
        self,
        output: SubtitleOutput,
        *,
        max_lines: int = 3,
        show_original: bool = False,
        deduplicator: SubtitleDeduplicator | None = None,
    ) -> None:
        self.output = output
        self.max_lines = max_lines
        self.show_original = show_original
        self.deduplicator = deduplicator or SubtitleDeduplicator()
        self._entries: deque[TranslationResult] = deque(maxlen=max_lines)

    def show(self, result: TranslationResult) -> bool:
        if self.deduplicator.is_duplicate(result.source_id, result.original):
            return False
        if self._entries.maxlen != self.max_lines:
            self._entries = deque(self._entries, maxlen=self.max_lines)
        self._entries.append(result)
        self._render()
        return True

    def update_options(self, *, max_lines: int, show_original: bool) -> None:
        self.max_lines = max(1, max_lines)
        self.show_original = show_original
        self._entries = deque(self._entries, maxlen=self.max_lines)
        self._render()

    def clear(self) -> None:
        self._entries.clear()
        self.deduplicator.clear()
        self.output.clear()

    def _render(self) -> None:
        lines = []
        for entry in self._entries:
            if self.show_original:
                lines.append(entry.original)
            lines.append(entry.translated)
        self.output.display(lines)

