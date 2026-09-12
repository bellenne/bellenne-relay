"""Replaceable speech recognition contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import SpeechSegment, TranscriptionResult


class SpeechRecognitionEngine(ABC):
    @abstractmethod
    def transcribe(
        self, segment: SpeechSegment, language: str = "en"
    ) -> TranscriptionResult:
        """Recognize a complete speech segment."""

    @abstractmethod
    def close(self) -> None:
        """Release model resources, if any."""
