"""Fallback standard streams for GUI-only Windows builds."""

from __future__ import annotations

import os
import sys
from typing import TextIO

_FALLBACK_STREAMS: list[TextIO] = []


def ensure_standard_streams() -> None:
    """Give libraries a writable sink when a windowed EXE has no console."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is not None:
            continue
        stream = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
        _FALLBACK_STREAMS.append(stream)
        setattr(sys, name, stream)
