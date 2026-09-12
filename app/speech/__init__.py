"""Speech recognition interfaces and workers."""

from .engine import SpeechRecognitionEngine
from .models import SpeechSegment, TranscriptionResult
from .whisper_engine import WhisperEngine

__all__ = [
    "SpeechRecognitionEngine",
    "SpeechSegment",
    "TranscriptionResult",
    "WhisperEngine",
]

