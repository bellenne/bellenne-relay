from __future__ import annotations

import numpy as np

from app.vad.silero import SileroVadEngine, VadSettings


def test_emits_segment_only_after_enough_trailing_silence() -> None:
    def detector(audio, options):
        del options
        return [{"start": 1000, "end": min(5000, audio.size)}]

    vad = SileroVadEngine(
        VadSettings(min_silence_ms=500, speech_pad_ms=100, evaluation_ms=1),
        detector=detector,
    )

    assert vad.feed(np.ones(8000, dtype=np.float32)) == []
    segments = vad.feed(np.zeros(4000, dtype=np.float32))

    assert len(segments) == 1
    assert segments[0].start_sample == 1000
    assert segments[0].end_sample == 5000
    assert segments[0].audio.size == 4000


def test_flush_finishes_ongoing_speech() -> None:
    def detector(audio, options):
        del options
        return [{"start": 512, "end": audio.size}]

    vad = SileroVadEngine(VadSettings(evaluation_ms=1), detector=detector)
    assert vad.feed(np.ones(4000, dtype=np.float32)) == []

    segments = vad.flush()

    assert len(segments) == 1
    assert segments[0].start_sample == 512
    assert segments[0].end_sample == 4000


def test_long_silence_is_bounded_and_absolute_timestamps_advance() -> None:
    def detector(audio, options):
        del audio, options
        return []

    vad = SileroVadEngine(VadSettings(evaluation_ms=1, speech_pad_ms=100), detector=detector)
    vad.feed(np.zeros(40_000, dtype=np.float32))

    assert vad._audio.size == 1600
    assert vad._base_sample == 38_400

