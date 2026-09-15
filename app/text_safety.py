"""Defensive text shaping for recognizer and UI output."""

from __future__ import annotations

import re

SOFT_BREAK = "\u200b"
_PATHOLOGICAL_RUN = re.compile(r"(\S)\1{31,}")
_LONG_TOKEN = re.compile(r"\S+")


def collapse_pathological_runs(text: str, *, kept_characters: int = 12) -> str:
    """Shorten recognizer loops such as a character repeated hundreds of times."""
    if kept_characters < 1:
        raise ValueError("kept_characters must be positive")
    return _PATHOLOGICAL_RUN.sub(
        lambda match: match.group(1) * kept_characters + "…",
        text,
    )


def soft_wrap_unbroken_text(text: str, *, chunk_size: int = 12) -> str:
    """Add invisible break opportunities without changing visible characters."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")

    def add_breaks(match: re.Match[str]) -> str:
        token = match.group(0).replace(SOFT_BREAK, "")
        if len(token) <= chunk_size:
            return token
        return SOFT_BREAK.join(
            token[index : index + chunk_size]
            for index in range(0, len(token), chunk_size)
        )

    return _LONG_TOKEN.sub(add_breaks, text)
