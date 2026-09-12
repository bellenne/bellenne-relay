"""Conservative suppression of immediate identical Whisper results."""

from __future__ import annotations

import re
import time
from collections import deque


class SubtitleDeduplicator:
    def __init__(self, duplicate_window_seconds: float = 4.0, history_size: int = 20) -> None:
        self.duplicate_window_seconds = duplicate_window_seconds
        self._recent: deque[tuple[str, str, float]] = deque(maxlen=history_size)

    def is_duplicate(
        self, source_id: str, text: str, timestamp: float | None = None
    ) -> bool:
        now = time.monotonic() if timestamp is None else timestamp
        normalized = _normalize(text)
        if not normalized:
            return True
        duplicate = any(
            previous_source == source_id
            and previous_text == normalized
            and now - previous_time <= self.duplicate_window_seconds
            for previous_source, previous_text, previous_time in self._recent
        )
        self._recent.append((source_id, normalized, now))
        return duplicate

    def clear(self) -> None:
        self._recent.clear()


def _normalize(text: str) -> str:
    return re.sub(r"[^\w]+", " ", text.casefold(), flags=re.UNICODE).strip()

