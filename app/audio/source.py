"""Non-blocking PortAudio capture source with a bounded PCM queue."""

from __future__ import annotations

import logging
import queue
import threading
import wave
from collections.abc import Callable
from contextlib import ExitStack, suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .devices import AudioDevice
from .errors import AudioCaptureError
from .levels import pcm16_peak_dbfs

LOGGER = logging.getLogger(__name__)


class AudioSourceState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class CaptureStats:
    peak_dbfs: float
    frames_written: int
    dropped_chunks: int
    callback_status_flags: int


class AudioCaptureSource:
    """Capture one endpoint without doing disk work in PortAudio's callback."""

    def __init__(
        self,
        audio: Any,
        pyaudio_module: Any,
        device: AudioDevice,
        output_path: Path | None,
        *,
        on_chunk: Callable[[bytes], None] | None = None,
        frames_per_buffer: int = 1024,
        queue_size: int = 256,
    ) -> None:
        self.audio = audio
        self.pyaudio = pyaudio_module
        self.device = device
        self.output_path = output_path
        self.on_chunk = on_chunk
        self.frames_per_buffer = frames_per_buffer
        self.state = AudioSourceState.STOPPED
        self.error: BaseException | None = None

        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=queue_size)
        self._stream: Any | None = None
        self._worker: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._stats_lock = threading.Lock()
        self._peak_dbfs = -96.0
        self._frames_written = 0
        self._dropped_chunks = 0
        self._callback_status_flags = 0

    def start(self) -> None:
        if self.state is not AudioSourceState.STOPPED:
            raise AudioCaptureError(f"Cannot start source in state {self.state.value}.")
        self.state = AudioSourceState.STARTING
        self.error = None
        self._stop_event.clear()
        if self.output_path is not None:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._worker = threading.Thread(
            target=self._write_worker,
            name=f"audio-writer-{self.device.kind.value}",
            daemon=False,
        )
        self._worker.start()

        try:
            self._stream = self.audio.open(
                format=self.pyaudio.paInt16,
                channels=self.device.channels,
                rate=self.device.sample_rate,
                frames_per_buffer=self.frames_per_buffer,
                input=True,
                input_device_index=self.device.capture_index,
                stream_callback=self._callback,
                start=False,
            )
            self._stream.start_stream()
        except BaseException as exc:
            self.error = exc
            self.state = AudioSourceState.ERROR
            self._stop_event.set()
            self._join_worker()
            raise AudioCaptureError(
                f"Failed to open {self.device.name!r}: {exc}"
            ) from exc

        self.state = AudioSourceState.RUNNING
        LOGGER.info(
            "Started %s capture: %s, index=%d, %d Hz, %d ch",
            self.device.kind.value,
            self.device.name,
            self.device.capture_index,
            self.device.sample_rate,
            self.device.channels,
        )

    def stop(self) -> None:
        if self.state is AudioSourceState.STOPPED:
            return
        self.state = AudioSourceState.STOPPING
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                if stream.is_active():
                    stream.stop_stream()
            finally:
                stream.close()
        self._stop_event.set()
        self._join_worker()
        self.state = AudioSourceState.ERROR if self.error else AudioSourceState.STOPPED
        LOGGER.info("Stopped %s capture", self.device.kind.value)

    def stats(self) -> CaptureStats:
        with self._stats_lock:
            return CaptureStats(
                peak_dbfs=self._peak_dbfs,
                frames_written=self._frames_written,
                dropped_chunks=self._dropped_chunks,
                callback_status_flags=self._callback_status_flags,
            )

    def is_stream_active(self) -> bool:
        stream = self._stream
        if self.state is not AudioSourceState.RUNNING or stream is None:
            return False
        try:
            return bool(stream.is_active())
        except OSError:
            return False

    def _callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict[str, float],
        status_flags: int,
    ) -> tuple[None, int]:
        del frame_count, time_info
        if status_flags:
            with self._stats_lock:
                self._callback_status_flags |= status_flags
        try:
            self._queue.put_nowait(in_data)
        except queue.Full:
            with suppress(queue.Empty):
                self._queue.get_nowait()
            with suppress(queue.Full):
                self._queue.put_nowait(in_data)
            with self._stats_lock:
                self._dropped_chunks += 1
        return None, self.pyaudio.paContinue

    def _write_worker(self) -> None:
        try:
            with ExitStack() as stack:
                output = (
                    stack.enter_context(wave.open(str(self.output_path), "wb"))
                    if self.output_path is not None
                    else None
                )
                if output is not None:
                    output.setnchannels(self.device.channels)
                    output.setsampwidth(self.audio.get_sample_size(self.pyaudio.paInt16))
                    output.setframerate(self.device.sample_rate)
                while not self._stop_event.is_set() or not self._queue.empty():
                    try:
                        chunk = self._queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    if output is not None:
                        output.writeframesraw(chunk)
                    if self.on_chunk is not None:
                        self.on_chunk(chunk)
                    frame_count = len(chunk) // (2 * self.device.channels)
                    peak = pcm16_peak_dbfs(chunk)
                    with self._stats_lock:
                        self._frames_written += frame_count
                        self._peak_dbfs = peak
        except BaseException as exc:
            LOGGER.exception("Audio writer failed for %s", self.device.name)
            self.error = exc
            self._stop_event.set()

    def _join_worker(self) -> None:
        if self._worker is not None:
            self._worker.join(timeout=5.0)
            if self._worker.is_alive():
                self.error = AudioCaptureError("Audio writer did not stop within 5 seconds.")
            self._worker = None
