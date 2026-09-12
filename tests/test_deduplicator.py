from __future__ import annotations

from app.subtitles import SubtitleDeduplicator


def test_suppresses_immediate_same_source_duplicate() -> None:
    deduplicator = SubtitleDeduplicator(duplicate_window_seconds=4)
    assert not deduplicator.is_duplicate("SYSTEM", "We need to go.", timestamp=10)
    assert deduplicator.is_duplicate("SYSTEM", " we need to GO! ", timestamp=12)


def test_allows_same_phrase_from_other_source_or_later() -> None:
    deduplicator = SubtitleDeduplicator(duplicate_window_seconds=4)
    assert not deduplicator.is_duplicate("SYSTEM", "Wait for me", timestamp=10)
    assert not deduplicator.is_duplicate("MICROPHONE", "Wait for me", timestamp=11)
    assert not deduplicator.is_duplicate("SYSTEM", "Wait for me", timestamp=20)

