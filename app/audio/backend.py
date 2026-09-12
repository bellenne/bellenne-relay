"""Small adapter around PyAudioWPatch.

Keeping the third-party import here lets device selection and most source logic be
unit-tested on machines without Windows audio hardware.
"""

from __future__ import annotations

import sys
from typing import Any

from .errors import AudioBackendUnavailable


def load_pyaudio() -> Any:
    """Import and return PyAudioWPatch with an actionable error on failure."""
    if sys.platform != "win32":
        raise AudioBackendUnavailable("WASAPI Loopback is supported only on Windows.")

    try:
        import pyaudiowpatch as pyaudio
    except (ImportError, OSError) as exc:
        raise AudioBackendUnavailable(
            "PyAudioWPatch is unavailable. Use Python 3.11 or 3.12 and run "
            "`python -m pip install -e .`."
        ) from exc
    return pyaudio

