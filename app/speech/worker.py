"""Bounded producer/consumer worker for Whisper inference."""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from contextlib import suppress

from .engine import SpeechRecognitionEngine
from .models import SpeechSegment, TranscriptionResult

LOGGER = logging.getLogger(__name__)


class TranscriptionWorker:
    def __init__(
        self,
        engine_factory: Callable[[], SpeechRecognitionEngine],
        on_result: Callable[[TranscriptionResult], None],
        *,
        language: str = "en",
        queue_size: int = 4,
    ) -> None:
        self._engine_factory = engine_factory
        self._on_result = on_result
        self._language = language
        self._queue: queue.Queue[SpeechSegment] = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._engine: SpeechRecognitionEngine | None = None
        self.error: BaseException | None = None
        self.dropped_segments = 0

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("Transcription worker is already started")
        self._stop_event.clear()
        self._ready_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="whisper-worker", daemon=False
        )
        self._thread.start()

    def wait_ready(self, timeout: float | None = None) -> bool:
        if not self._ready_event.wait(timeout):
            return False
        if self.error is not None:
            raise RuntimeError(f"Whisper worker failed: {self.error}") from self.error
        return True

    def submit(self, segment: SpeechSegment) -> None:
        if self._stop_event.is_set():
            return
        try:
            self._queue.put_nowait(segment)
        except queue.Full:
            with suppress(queue.Empty):
                self._queue.get_nowait()
            with suppress(queue.Full):
                self._queue.put_nowait(segment)
            self.dropped_segments += 1
            LOGGER.warning("Whisper queue overflow; discarded the oldest speech segment")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=30.0)
            if self._thread.is_alive():
                raise RuntimeError("Whisper worker did not stop within 30 seconds")
            self._thread = None

    def _run(self) -> None:
        try:
            self._engine = self._engine_factory()
            self._ready_event.set()
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    segment = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                result = self._engine.transcribe(segment, self._language)
                if result.text:
                    self._on_result(result)
        except BaseException as exc:
            self.error = exc
            LOGGER.exception("Whisper worker failed")
            self._ready_event.set()
            self._stop_event.set()
        finally:
            if self._engine is not None:
                self._engine.close()
                self._engine = None
