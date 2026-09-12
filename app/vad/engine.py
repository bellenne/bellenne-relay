"""Replaceable VAD contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class VadSegment:
    audio: NDArray[np.float32]
    start_sample: int
    end_sample: int


class VadEngine(ABC):
    @abstractmethod
    def feed(self, audio: NDArray[np.float32]) -> list[VadSegment]:
        """Accept continuous 16 kHz mono samples and return completed speech."""

    @abstractmethod
    def flush(self) -> list[VadSegment]:
        """Finalize suitable speech remaining at shutdown."""

