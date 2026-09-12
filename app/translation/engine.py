"""Translation contract independent of Marian, local models or APIs."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationEngine(ABC):
    @abstractmethod
    def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        """Translate a formed text fragment."""

    @abstractmethod
    def close(self) -> None:
        """Release model resources."""

