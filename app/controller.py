"""Thread-safe state machine coordinating the complete local pipeline."""

from __future__ import annotations

import functools
import logging
import queue
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from app.audio.backend import load_pyaudio
from app.audio.devices import AudioDeviceManager, AudioDeviceType
from app.audio.source import AudioCaptureSource
from app.config import AppSettings
from app.runtime_paths import runtime_paths
from app.speech.whisper_engine import WhisperEngine
from app.speech.worker import TranscriptionWorker
from app.state import ApplicationState
from app.translation import MarianTranslationEngine
from app.translation.worker import TranslationWorker
from app.vad import SileroVadEngine, VadSettings
from app.workers import SourceSpeechPipeline

LOGGER = logging.getLogger(__name__)


class PipelineController(QObject):
    state_changed = Signal(str)
    devices_ready = Signal(object, object)
    translation_ready = Signal(object)
    component_changed = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(
        self,
        model_root: Path | None = None,
        *,
        bundled_model_root: Path | None = None,
    ) -> None:
        super().__init__()
        self._model_root = model_root or runtime_paths().models
        self._bundled_model_root = bundled_model_root
        self._state = ApplicationState.STOPPED
        self._state_lock = threading.Lock()
        self._resource_lock = threading.Lock()
        self._commands: queue.Queue[tuple[str, AppSettings | None]] = queue.Queue()
        self._control_thread = threading.Thread(
            target=self._control_loop,
            name="pipeline-controller",
            daemon=False,
        )
        self._control_thread.start()
        self._audio: Any | None = None
        self._pa: Any | None = None
        self._sources: list[AudioCaptureSource] = []
        self._pipelines: list[SourceSpeechPipeline] = []
        self._transcriber: TranscriptionWorker | None = None
        self._translator: TranslationWorker | None = None
        self._active_settings: AppSettings | None = None

    @property
    def state(self) -> ApplicationState:
        with self._state_lock:
            return self._state

    def refresh_devices(self) -> None:
        self._commands.put(("refresh", None))

    def start(self, settings: AppSettings) -> bool:
        with self._state_lock:
            if self._state not in (ApplicationState.STOPPED, ApplicationState.ERROR):
                return False
            self._state = ApplicationState.INITIALIZING
        self.state_changed.emit(ApplicationState.INITIALIZING.value)
        self._commands.put(("start", replace(settings)))
        return True

    def stop(self) -> bool:
        with self._state_lock:
            if self._state not in (ApplicationState.INITIALIZING, ApplicationState.RUNNING):
                return False
            self._state = ApplicationState.STOPPING
        self.state_changed.emit(ApplicationState.STOPPING.value)
        self._commands.put(("stop", None))
        return True

    def levels(self) -> dict[str, float]:
        with self._resource_lock:
            sources = list(self._sources)
        return {source.device.kind.value: source.stats().peak_dbfs for source in sources}

    def health_error(self) -> str | None:
        with self._resource_lock:
            errors = [
                *(source.error for source in self._sources),
                *(pipeline.error for pipeline in self._pipelines),
                self._transcriber.error if self._transcriber else None,
                self._translator.error if self._translator else None,
            ]
        return next((str(error) for error in errors if error is not None), None)

    def shutdown(self) -> None:
        self._commands.put(("shutdown", None))
        self._control_thread.join(timeout=60.0)
        if self._control_thread.is_alive():
            LOGGER.error("Pipeline controller did not stop within 60 seconds")

    def _control_loop(self) -> None:
        while True:
            try:
                command, settings = self._commands.get(timeout=1.0)
            except queue.Empty:
                self._monitor_pipeline()
                continue
            if command == "shutdown":
                self._stop_pipeline()
                return
            if command == "refresh":
                self._discover_devices()
                continue
            if command == "start" and settings is not None:
                self._start_pipeline(settings)
                continue
            if command == "stop":
                self._stop_pipeline()

    def _discover_devices(self) -> None:
        if self.state not in (ApplicationState.STOPPED, ApplicationState.ERROR):
            return
        try:
            pa = load_pyaudio()
            with pa.PyAudio() as audio:
                manager = AudioDeviceManager(audio, pa.paWASAPI)
                self.devices_ready.emit(
                    manager.list_system_outputs(), manager.list_microphones()
                )
        except Exception as exc:
            LOGGER.exception("Device discovery failed")
            self.error_occurred.emit(str(exc))

    def _start_pipeline(self, settings: AppSettings) -> None:
        try:
            self._active_settings = settings
            self.component_changed.emit("whisper", "loading")
            self.component_changed.emit("translator", "loading")
            translator_model: str | Path = settings.translation_model
            translator_offline = False
            whisper_model: str | Path = settings.whisper_model
            whisper_offline = False
            if self._bundled_model_root is not None:
                translation_candidate = (
                    self._bundled_model_root
                    / "translation"
                    / f"{settings.source_language}-{settings.target_language}"
                )
                whisper_candidate = (
                    self._bundled_model_root / "whisper" / settings.whisper_model
                )
                if translation_candidate.is_dir():
                    translator_model = translation_candidate
                    translator_offline = True
                if whisper_candidate.is_dir():
                    whisper_model = whisper_candidate
                    whisper_offline = True
            translator = TranslationWorker(
                functools.partial(
                    MarianTranslationEngine,
                    str(translator_model),
                    source_language=settings.source_language,
                    target_language=settings.target_language,
                    device=settings.translation_device,
                    cache_dir=self._model_root / "translation",
                    offline=translator_offline,
                ),
                self.translation_ready.emit,
                source_language=settings.source_language,
                target_language=settings.target_language,
            )
            transcriber = TranscriptionWorker(
                functools.partial(
                    WhisperEngine,
                    str(whisper_model),
                    compute_device=settings.compute_device,
                    cpu_threads=settings.whisper_cpu_threads,
                    filter_source_language=settings.filter_source_language,
                    language_filter_threshold=settings.language_filter_threshold,
                    download_root=self._model_root / "whisper",
                    offline=whisper_offline,
                ),
                translator.submit,
                language=settings.source_language,
            )
            with self._resource_lock:
                self._translator = translator
                self._transcriber = transcriber
            translator.start()
            transcriber.start()
            translator.wait_ready()
            self.component_changed.emit("translator", "ready")
            transcriber.wait_ready()
            self.component_changed.emit("whisper", "ready")

            pa = load_pyaudio()
            audio = pa.PyAudio()
            manager = AudioDeviceManager(audio, pa.paWASAPI)
            devices = []
            if settings.audio_source in ("system", "both"):
                devices.append(
                    manager.resolve(AudioDeviceType.SYSTEM, settings.system_device)
                )
            if settings.audio_source in ("microphone", "both"):
                devices.append(
                    manager.resolve(
                        AudioDeviceType.MICROPHONE, settings.microphone_device
                    )
                )
            vad_settings = VadSettings(
                threshold=settings.vad_threshold,
                min_speech_ms=settings.vad_min_speech_ms,
                min_silence_ms=settings.vad_min_silence_ms,
                max_speech_seconds=settings.vad_max_speech_seconds,
            )
            pipelines = []
            sources = []
            for device in devices:
                pipeline = SourceSpeechPipeline(
                    device, SileroVadEngine(vad_settings), transcriber.submit
                )
                source = AudioCaptureSource(
                    audio,
                    pa,
                    device,
                    output_path=None,
                    on_chunk=pipeline.submit_pcm,
                )
                pipelines.append(pipeline)
                sources.append(source)
            with self._resource_lock:
                self._pa = pa
                self._audio = audio
                self._pipelines = pipelines
                self._sources = sources
            for pipeline in pipelines:
                pipeline.start()
            for source in sources:
                source.start()
                self.component_changed.emit(source.device.kind.value, "active")
            with self._state_lock:
                stopping = self._state is ApplicationState.STOPPING
            if not stopping:
                self._set_state(ApplicationState.RUNNING)
        except Exception as exc:
            LOGGER.exception("Pipeline initialization failed")
            self.error_occurred.emit(str(exc))
            self._stop_pipeline(final_state=ApplicationState.ERROR)

    def _stop_pipeline(
        self, final_state: ApplicationState = ApplicationState.STOPPED
    ) -> None:
        with self._resource_lock:
            sources = self._sources
            pipelines = self._pipelines
            transcriber = self._transcriber
            translator = self._translator
            audio = self._audio
            self._sources = []
            self._pipelines = []
            self._transcriber = None
            self._translator = None
            self._audio = None
            self._pa = None
            self._active_settings = None
        try:
            for source in reversed(sources):
                source.stop()
                self.component_changed.emit(source.device.kind.value, "stopped")
            for pipeline in reversed(pipelines):
                pipeline.stop()
            if transcriber is not None:
                transcriber.stop()
                self.component_changed.emit("whisper", "stopped")
            if translator is not None:
                translator.stop()
                self.component_changed.emit("translator", "stopped")
            if audio is not None:
                audio.terminate()
        except Exception as exc:
            LOGGER.exception("Pipeline shutdown failed")
            self.error_occurred.emit(str(exc))
            final_state = ApplicationState.ERROR
        self._set_state(final_state)

    def _monitor_pipeline(self) -> None:
        if self.state is not ApplicationState.RUNNING:
            return
        with self._resource_lock:
            sources = list(self._sources)
            audio = self._audio
            pa = self._pa
            settings = self._active_settings
        inactive = next((source for source in sources if not source.is_stream_active()), None)
        if inactive is not None:
            message = (
                f"{inactive.device.kind.value.title()} device became unavailable: "
                f"{inactive.device.name}. Reconnect it and press Start again."
            )
            LOGGER.error(message)
            self.error_occurred.emit(message)
            self._stop_pipeline(final_state=ApplicationState.ERROR)
            return
        if audio is None or pa is None or settings is None:
            return
        manager = AudioDeviceManager(audio, pa.paWASAPI)
        try:
            if settings.system_device == "default" and settings.audio_source in (
                "system",
                "both",
            ):
                current = manager.default_system_output()
                captured = next(
                    item for item in sources if item.device.kind is AudioDeviceType.SYSTEM
                )
                if current.physical_index != captured.device.physical_index:
                    self._default_changed("output", current.name)
                    return
            if settings.microphone_device == "default" and settings.audio_source in (
                "microphone",
                "both",
            ):
                current = manager.default_microphone()
                captured = next(
                    item
                    for item in sources
                    if item.device.kind is AudioDeviceType.MICROPHONE
                )
                if current.physical_index != captured.device.physical_index:
                    self._default_changed("microphone", current.name)
        except Exception as exc:
            LOGGER.warning("Audio device health check failed: %s", exc)

    def _default_changed(self, kind: str, new_name: str) -> None:
        message = (
            f"Windows default {kind} changed to {new_name}. "
            "Capture was stopped; press Start to reconnect."
        )
        LOGGER.warning(message)
        self.error_occurred.emit(message)
        self._stop_pipeline(final_state=ApplicationState.ERROR)

    def _set_state(self, state: ApplicationState) -> None:
        with self._state_lock:
            self._state = state
        self.state_changed.emit(state.value)
