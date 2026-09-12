"""Conversion of native interleaved PCM into Whisper-ready audio."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatAudio = NDArray[np.float32]


class AudioProcessor:
    """Downmix, normalize and continuously resample signed 16-bit PCM."""

    OUTPUT_RATE = 16_000

    def __init__(self, input_rate: int, channels: int) -> None:
        if input_rate <= 0:
            raise ValueError("input_rate must be positive")
        if channels <= 0:
            raise ValueError("channels must be positive")
        self.input_rate = input_rate
        self.channels = channels
        self._step = input_rate / self.OUTPUT_RATE
        self._processed_samples = 0
        self._next_output_position = 0.0
        self._tail: np.float32 | None = None

    def process_pcm16(self, data: bytes) -> FloatAudio:
        """Convert a native chunk while preserving resampling phase across chunks."""
        sample_count = len(data) // 2
        complete_count = sample_count - sample_count % self.channels
        if complete_count == 0:
            return np.empty(0, dtype=np.float32)

        pcm = np.frombuffer(data, dtype="<i2", count=complete_count)
        frames = pcm.reshape(-1, self.channels).astype(np.float32)
        mono = frames.mean(axis=1) / 32768.0
        if self.input_rate == self.OUTPUT_RATE:
            self._processed_samples += mono.size
            self._tail = mono[-1]
            return np.ascontiguousarray(mono, dtype=np.float32)
        return self._resample(mono)

    def reset(self) -> None:
        self._processed_samples = 0
        self._next_output_position = 0.0
        self._tail = None

    def _resample(self, mono: FloatAudio) -> FloatAudio:
        chunk_start = self._processed_samples
        chunk_end = chunk_start + mono.size - 1
        if self._tail is None:
            values = mono
            value_start = chunk_start
        else:
            values = np.concatenate((np.asarray([self._tail], dtype=np.float32), mono))
            value_start = chunk_start - 1

        if self._next_output_position > chunk_end:
            result = np.empty(0, dtype=np.float32)
        else:
            positions = np.arange(
                self._next_output_position,
                chunk_end + 1e-9,
                self._step,
                dtype=np.float64,
            )
            coordinates = np.arange(value_start, chunk_end + 1, dtype=np.float64)
            result = np.interp(positions, coordinates, values).astype(np.float32)
            self._next_output_position += positions.size * self._step

        self._processed_samples += mono.size
        self._tail = mono[-1]
        return result

