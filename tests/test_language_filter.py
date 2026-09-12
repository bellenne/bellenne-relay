from app.speech.whisper_engine import should_reject_language


def test_confident_wrong_language_is_rejected() -> None:
    assert should_reject_language(
        expected="en", detected="ru", probability=0.94, threshold=0.65
    )
    assert should_reject_language(
        expected="ru", detected="en", probability=0.88, threshold=0.65
    )


def test_expected_or_ambiguous_language_is_kept() -> None:
    assert not should_reject_language(
        expected="en", detected="en", probability=0.99, threshold=0.65
    )
    assert not should_reject_language(
        expected="en", detected="ru", probability=0.42, threshold=0.65
    )
