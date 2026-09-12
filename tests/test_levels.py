from __future__ import annotations

import math
import struct

from app.audio.levels import level_bar, pcm16_peak_dbfs


def test_silence_has_floor_level() -> None:
    assert pcm16_peak_dbfs(b"\x00\x00" * 16) == -96.0


def test_full_scale_peak_is_zero_dbfs() -> None:
    assert math.isclose(pcm16_peak_dbfs(struct.pack("<h", 32767)), 0.0, abs_tol=0.001)


def test_half_scale_peak_is_about_minus_six_dbfs() -> None:
    assert math.isclose(pcm16_peak_dbfs(struct.pack("<h", 16384)), -6.02, abs_tol=0.02)


def test_level_bar_has_fixed_width() -> None:
    assert level_bar(-96.0, 10) == "░" * 10
    assert level_bar(0.0, 10) == "█" * 10

