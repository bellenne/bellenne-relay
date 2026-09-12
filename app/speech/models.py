"""Data transferred between the audio, VAD and speech layers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    audio: NDArray[np.float32]
    source_id: str
    start_time: float
    end_time: float
    created_at: float

    @property
    def duration(self) -> float:
        return self.audio.size / 16_000


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    source_id: str
    start_time: float
    end_time: float
    confidence: float | None
    audio_duration: float
    processing_seconds: float
    total_latency_seconds: float

