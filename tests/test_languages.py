from __future__ import annotations

import pytest

from app.languages import language_pair, language_pair_from_key


def test_both_translation_directions_are_configured() -> None:
    forward = language_pair("en", "ru")
    reverse = language_pair_from_key("ru-en")

    assert forward.model_name.endswith("opus-mt-en-ru")
    assert reverse.model_name.endswith("opus-mt-ru-en")
    assert reverse.label == "Russian → English"


def test_unknown_translation_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported translation direction"):
        language_pair("en", "de")
