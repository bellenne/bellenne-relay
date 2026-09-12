from __future__ import annotations

import time

from app.speech.models import TranscriptionResult
from app.translation.engine import TranslationEngine
from app.translation.models import TranslationResult
from app.translation.worker import TranslationWorker


class FakeTranslationEngine(TranslationEngine):
    def translate(self, text: str, source_language: str, target_language: str) -> str:
        assert (source_language, target_language) == ("en", "ru")
        return f"RU({text})"

    def close(self) -> None:
        pass


class FakeReverseTranslationEngine(TranslationEngine):
    def translate(self, text: str, source_language: str, target_language: str) -> str:
        assert (source_language, target_language) == ("ru", "en")
        return f"EN({text})"

    def close(self) -> None:
        pass


def transcription(text: str = "Hello") -> TranscriptionResult:
    now = time.monotonic()
    return TranscriptionResult(
        text=text,
        source_id="SYSTEM",
        start_time=now - 1.0,
        end_time=now,
        confidence=0.9,
        audio_duration=1.0,
        processing_seconds=0.1,
        total_latency_seconds=0.2,
    )


def test_translation_engine_interface_is_replaceable() -> None:
    engine: TranslationEngine = FakeTranslationEngine()
    assert engine.translate("Hello", "en", "ru") == "RU(Hello)"


def test_translation_worker_processes_completed_text() -> None:
    results: list[TranslationResult] = []
    worker = TranslationWorker(FakeTranslationEngine, results.append)
    worker.start()
    assert worker.wait_ready(timeout=1)

    worker.submit(transcription())
    worker.stop()

    assert len(results) == 1
    assert results[0].original == "Hello"
    assert results[0].translated == "RU(Hello)"


def test_translation_worker_ignores_empty_text() -> None:
    worker = TranslationWorker(FakeTranslationEngine, lambda result: None)
    worker.submit(transcription(""))
    assert worker._queue.empty()


def test_translation_worker_supports_reverse_direction() -> None:
    results: list[TranslationResult] = []
    worker = TranslationWorker(
        FakeReverseTranslationEngine,
        results.append,
        source_language="ru",
        target_language="en",
    )
    worker.start()
    assert worker.wait_ready(timeout=1)

    worker.submit(transcription("Привет"))
    worker.stop()

    assert results[0].translated == "EN(Привет)"
