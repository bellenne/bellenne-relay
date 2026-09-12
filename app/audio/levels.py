"""PCM level helpers that do not depend on NumPy."""

from __future__ import annotations

import math
from array import array


def pcm16_peak_dbfs(data: bytes) -> float:
    """Return peak dBFS for little-endian signed 16-bit PCM."""
    if not data:
        return -96.0
    samples = array("h")
    samples.frombytes(data[: len(data) - (len(data) % 2)])
    if not samples:
        return -96.0
    peak = max(abs(sample) for sample in samples)
    if peak == 0:
        return -96.0
    return max(-96.0, 20.0 * math.log10(peak / 32767.0))


def level_bar(dbfs: float, width: int = 20) -> str:
    """Render a compact -60..0 dBFS meter."""
    fraction = min(1.0, max(0.0, (dbfs + 60.0) / 60.0))
    filled = round(width * fraction)
    return "█" * filled + "░" * (width - filled)

