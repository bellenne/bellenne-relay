from __future__ import annotations

import math
import struct

import numpy as np

from app.audio.processor import AudioProcessor


def test_downmixes_stereo_pcm_to_normalized_mono() -> None:
    processor = AudioProcessor(input_rate=16_000, channels=2)
    pcm = struct.pack("<hhhh", 32767, -32768, 16384, 16384)

    result = processor.process_pcm16(pcm)

    assert result.dtype == np.float32
    assert result.shape == (2,)
    assert math.isclose(float(result[0]), -1 / 65536, abs_tol=1e-6)
    assert math.isclose(float(result[1]), 0.5, abs_tol=1e-6)


def test_resamples_48khz_to_16khz() -> None:
    processor = AudioProcessor(input_rate=48_000, channels=1)
    pcm = np.arange(480, dtype=np.int16).tobytes()

    result = processor.process_pcm16(pcm)

    assert result.shape == (160,)
    assert np.allclose(result[:4] * 32768, [0, 3, 6, 9])


def test_resampler_preserves_phase_between_chunks() -> None:
    whole = AudioProcessor(input_rate=44_100, channels=1)
    split = AudioProcessor(input_rate=44_100, channels=1)
    pcm = np.arange(1000, dtype=np.int16)

    expected = whole.process_pcm16(pcm.tobytes())
    actual = np.concatenate(
        [split.process_pcm16(pcm[:333].tobytes()), split.process_pcm16(pcm[333:].tobytes())]
    )

    assert actual.shape == expected.shape
    assert np.allclose(actual, expected)


def test_empty_or_partial_frame_returns_empty_array() -> None:
    processor = AudioProcessor(input_rate=48_000, channels=2)
    assert processor.process_pcm16(b"\x00\x00").size == 0

