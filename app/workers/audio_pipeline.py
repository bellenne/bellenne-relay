"""Per-source PCM processing and VAD worker."""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable
from contextlib import suppress

from app.audio.devices import AudioDevice
from app.audio.processor import AudioProcessor
from app.speech.models import SpeechSegment
from app.vad.engine import VadEngine

LOGGER = logging.getLogger(__name__)


class SourceSpeechPipeline:
    """Keep processing/VAD for one source independent from every other source."""

    def __init__(
        self,
        device: AudioDevice,
        vad: VadEngine,
        on_segment: Callable[[SpeechSegment], None],
        *,
        queue_size: int = 128,
    ) -> None:
        self.device = device
        self._processor = AudioProcessor(device.sample_rate, device.channels)
        self._vad = vad
        self._on_segment = on_segment
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_at = 0.0
        self.dropped_chunks = 0
        self.error: BaseException | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("Source speech pipeline is already started")
        self._started_at = time.monotonic()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"speech-segmenter-{self.device.kind.value}",
            daemon=False,
        )
        self._thread.start()

    def submit_pcm(self, data: bytes) -> None:
        try:
            self._queue.put_nowait(data)
        except queue.Full:
            with suppress(queue.Empty):
                self._queue.get_nowait()
            with suppress(queue.Full):
                self._queue.put_nowait(data)
            self.dropped_chunks += 1
            LOGGER.warning("%s processing queue overflow", self.device.kind.value)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=10.0)
            if self._thread.is_alive():
                raise RuntimeError(
                    f"{self.device.kind.value} processor did not stop within 10 seconds"
                )
            self._thread = None

    def _run(self) -> None:
        try:
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    pcm = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                normalized = self._processor.process_pcm16(pcm)
                self._emit(self._vad.feed(normalized))
            self._emit(self._vad.flush())
        except BaseException as exc:
            self.error = exc
            self._stop_event.set()
            LOGGER.exception("%s speech pipeline failed", self.device.kind.value)

    def _emit(self, vad_segments: list) -> None:
        for item in vad_segments:
            self._on_segment(
                SpeechSegment(
                    audio=item.audio,
                    source_id=self.device.kind.value.upper(),
                    start_time=self._started_at + item.start_sample / 16_000,
                    end_time=self._started_at + item.end_sample / 16_000,
                    created_at=time.monotonic(),
                )
            )
