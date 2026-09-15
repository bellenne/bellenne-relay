"""Bounded producer/consumer worker for completed phrase translation."""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable
from contextlib import suppress

from app.speech.models import TranscriptionResult
from app.text_safety import collapse_pathological_runs

from .engine import TranslationEngine
from .models import TranslationResult

LOGGER = logging.getLogger(__name__)


class TranslationWorker:
    def __init__(
        self,
        engine_factory: Callable[[], TranslationEngine],
        on_result: Callable[[TranslationResult], None],
        *,
        source_language: str = "en",
        target_language: str = "ru",
        queue_size: int = 8,
    ) -> None:
        self._engine_factory = engine_factory
        self._on_result = on_result
        self._source_language = source_language
        self._target_language = target_language
        self._queue: queue.Queue[TranscriptionResult] = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._engine: TranslationEngine | None = None
        self.error: BaseException | None = None
        self.dropped_transcriptions = 0

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("Translation worker is already started")
        self._stop_event.clear()
        self._ready_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="translation-worker", daemon=False
        )
        self._thread.start()

    def wait_ready(self, timeout: float | None = None) -> bool:
        if not self._ready_event.wait(timeout):
            return False
        if self.error is not None:
            raise RuntimeError(f"Translation worker failed: {self.error}") from self.error
        return True

    def submit(self, result: TranscriptionResult) -> None:
        if not result.text or self._stop_event.is_set():
            return
        try:
            self._queue.put_nowait(result)
        except queue.Full:
            with suppress(queue.Empty):
                self._queue.get_nowait()
            with suppress(queue.Full):
                self._queue.put_nowait(result)
            self.dropped_transcriptions += 1
            LOGGER.warning("Translation queue overflow; discarded the oldest text")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=30.0)
            if self._thread.is_alive():
                raise RuntimeError("Translation worker did not stop within 30 seconds")
            self._thread = None

    def _run(self) -> None:
        try:
            self._engine = self._engine_factory()
            self._ready_event.set()
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    transcription = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                original = collapse_pathological_runs(transcription.text)
                if original != transcription.text:
                    LOGGER.warning("Collapsed a pathological repeated-character transcription")
                started = time.monotonic()
                translated = self._engine.translate(
                    original,
                    self._source_language,
                    self._target_language,
                )
                translated = collapse_pathological_runs(translated)
                finished = time.monotonic()
                if translated:
                    self._on_result(
                        TranslationResult(
                            source_id=transcription.source_id,
                            original=original,
                            translated=translated,
                            audio_duration=transcription.audio_duration,
                            transcription_seconds=transcription.processing_seconds,
                            translation_seconds=finished - started,
                            total_latency_seconds=finished - transcription.end_time,
                            confidence=transcription.confidence,
                        )
                    )
        except BaseException as exc:
            self.error = exc
            self._ready_event.set()
            self._stop_event.set()
            LOGGER.exception("Translation worker failed")
        finally:
            if self._engine is not None:
                self._engine.close()
                self._engine = None
