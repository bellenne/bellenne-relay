"""Translation pipeline results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranslationResult:
    source_id: str
    original: str
    translated: str
    audio_duration: float
    transcription_seconds: float
    translation_seconds: float
    total_latency_seconds: float
    confidence: float | None

