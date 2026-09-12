"""Streaming segmenter powered by faster-whisper's bundled Silero VAD."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from faster_whisper.vad import VadOptions, get_speech_timestamps
from numpy.typing import NDArray

from .engine import VadEngine, VadSegment

Detector = Callable[[NDArray[np.float32], VadOptions], list[dict[str, int]]]
_MODEL_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class VadSettings:
    threshold: float = 0.5
    min_speech_ms: int = 200
    min_silence_ms: int = 500
    speech_pad_ms: int = 120
    max_speech_seconds: float = 10.0
    evaluation_ms: int = 160

    def __post_init__(self) -> None:
        if not 0 < self.threshold < 1:
            raise ValueError("VAD threshold must be between zero and one")
        if self.min_speech_ms < 0 or self.min_silence_ms <= 0:
            raise ValueError("VAD durations must be non-negative")
        if self.speech_pad_ms < 0 or self.max_speech_seconds <= 0:
            raise ValueError("VAD padding/max duration is invalid")
        if self.evaluation_ms <= 0:
            raise ValueError("VAD evaluation interval must be positive")


class SileroVadEngine(VadEngine):
    """Accumulate a small rolling buffer and emit only finalized Silero spans."""

    SAMPLE_RATE = 16_000

    def __init__(
        self,
        settings: VadSettings | None = None,
        *,
        detector: Detector | None = None,
    ) -> None:
        self.settings = settings or VadSettings()
        self._detector = detector or _detect_speech
        self._audio = np.empty(0, dtype=np.float32)
        self._base_sample = 0
        self._samples_since_evaluation = 0
        self._options = VadOptions(
            threshold=self.settings.threshold,
            min_speech_duration_ms=self.settings.min_speech_ms,
            max_speech_duration_s=self.settings.max_speech_seconds,
            min_silence_duration_ms=self.settings.min_silence_ms,
            speech_pad_ms=self.settings.speech_pad_ms,
        )

    def feed(self, audio: NDArray[np.float32]) -> list[VadSegment]:
        if audio.ndim != 1:
            raise ValueError("VAD input must be one-dimensional mono audio")
        if audio.size == 0:
            return []
        chunk = np.ascontiguousarray(audio, dtype=np.float32)
        self._audio = np.concatenate((self._audio, chunk))
        self._samples_since_evaluation += chunk.size
        evaluation_samples = self.settings.evaluation_ms * self.SAMPLE_RATE // 1000
        if self._samples_since_evaluation < evaluation_samples:
            return []
        self._samples_since_evaluation = 0
        return self._extract(flush=False)

    def flush(self) -> list[VadSegment]:
        segments = self._extract(flush=True)
        self._base_sample += self._audio.size
        self._audio = np.empty(0, dtype=np.float32)
        self._samples_since_evaluation = 0
        return segments

    def _extract(self, *, flush: bool) -> list[VadSegment]:
        if self._audio.size < 512:
            return []
        timestamps = self._detector(self._audio, self._options)
        if not timestamps:
            self._trim_leading_silence()
            return []

        trailing_required = max(
            1,
            (self.settings.min_silence_ms - self.settings.speech_pad_ms)
            * self.SAMPLE_RATE
            // 1000,
        )
        complete: list[dict[str, int]] = []
        for index, timestamp in enumerate(timestamps):
            is_followed_by_another = index < len(timestamps) - 1
            has_trailing_silence = self._audio.size - timestamp["end"] >= trailing_required
            if flush or is_followed_by_another or has_trailing_silence:
                complete.append(timestamp)

        if not complete:
            return []

        result = [
            VadSegment(
                audio=self._audio[item["start"] : item["end"]].copy(),
                start_sample=self._base_sample + item["start"],
                end_sample=self._base_sample + item["end"],
            )
            for item in complete
        ]
        consumed = complete[-1]["end"]
        self._audio = self._audio[consumed:].copy()
        self._base_sample += consumed
        return result

    def _trim_leading_silence(self) -> None:
        keep_samples = max(512, self.settings.speech_pad_ms * self.SAMPLE_RATE // 1000)
        trim_after = max(self.SAMPLE_RATE * 2, keep_samples * 2)
        if self._audio.size <= trim_after:
            return
        removed = self._audio.size - keep_samples
        self._audio = self._audio[-keep_samples:].copy()
        self._base_sample += removed


def _detect_speech(
    audio: NDArray[np.float32], options: VadOptions
) -> list[dict[str, int]]:
    # faster-whisper caches one ONNX Silero model. Serialize access so SYSTEM and
    # MICROPHONE keep independent buffers without racing the shared inference session.
    with _MODEL_LOCK:
        return get_speech_timestamps(audio, options, sampling_rate=16_000)

