"""Supported local translation directions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LanguagePair:
    source: str
    target: str
    source_name: str
    target_name: str
    model_name: str

    @property
    def key(self) -> str:
        return f"{self.source}-{self.target}"

    @property
    def label(self) -> str:
        return f"{self.source_name} → {self.target_name}"


SUPPORTED_LANGUAGE_PAIRS = (
    LanguagePair(
        source="en",
        target="ru",
        source_name="English",
        target_name="Russian",
        model_name="Helsinki-NLP/opus-mt-en-ru",
    ),
    LanguagePair(
        source="ru",
        target="en",
        source_name="Russian",
        target_name="English",
        model_name="Helsinki-NLP/opus-mt-ru-en",
    ),
)


def language_pair(source: str, target: str) -> LanguagePair:
    for pair in SUPPORTED_LANGUAGE_PAIRS:
        if (pair.source, pair.target) == (source, target):
            return pair
    raise ValueError(f"Unsupported translation direction: {source}→{target}")


def language_pair_from_key(key: str) -> LanguagePair:
    for pair in SUPPORTED_LANGUAGE_PAIRS:
        if pair.key == key:
            return pair
    raise ValueError(f"Unsupported translation direction: {key}")
