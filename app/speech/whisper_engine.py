"""faster-whisper implementation of the recognition contract."""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path
from typing import Literal

import numpy as np

from app.gpu_runtime import configure_gpu_dll_search

from .engine import SpeechRecognitionEngine
from .models import SpeechSegment, TranscriptionResult

LOGGER = logging.getLogger(__name__)
ComputeDevice = Literal["auto", "cpu", "cuda"]


class WhisperEngine(SpeechRecognitionEngine):
    """One lazily selected CTranslate2 Whisper model."""

    def __init__(
        self,
        model_size: str = "turbo",
        *,
        compute_device: ComputeDevice = "auto",
        cpu_threads: int = 8,
        filter_source_language: bool = True,
        language_filter_threshold: float = 0.65,
        download_root: Path = Path("models/whisper"),
        offline: bool = False,
    ) -> None:
        configure_gpu_dll_search()
        from faster_whisper import WhisperModel

        self.model_size = model_size
        self._model_class = WhisperModel
        self._requested_device = compute_device
        self._cpu_threads = max(1, cpu_threads)
        self._filter_source_language = filter_source_language
        self._language_filter_threshold = language_filter_threshold
        self._download_root = download_root
        self._offline = offline
        selected = resolve_compute_device(compute_device)
        download_root.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Loading Whisper %s on %s", model_size, selected)
        try:
            self._model = self._load_model(selected)
            if selected == "cuda":
                self._warmup_cuda()
        except Exception:
            if compute_device != "auto" or selected != "cuda":
                raise
            LOGGER.exception("CUDA Whisper initialization failed; falling back to CPU int8")
            selected = "cpu"
            self._model = self._load_model("cpu")
        self.device = selected
        LOGGER.info("Whisper %s is ready on %s", model_size, selected)

    def transcribe(
        self, segment: SpeechSegment, language: str = "en"
    ) -> TranscriptionResult:
        started = time.monotonic()
        try:
            realized = self._decode(segment, language)
        except (RuntimeError, OSError):
            if self._requested_device != "auto" or self.device != "cuda":
                raise
            LOGGER.exception("CUDA Whisper inference failed; retrying this segment on CPU int8")
            self._fallback_to_cpu()
            realized = self._decode(segment, language)
        text = " ".join(part.text.strip() for part in realized if part.text.strip()).strip()
        probabilities = [math.exp(part.avg_logprob) for part in realized]
        confidence = sum(probabilities) / len(probabilities) if probabilities else None
        finished = time.monotonic()
        return TranscriptionResult(
            text=text,
            source_id=segment.source_id,
            start_time=segment.start_time,
            end_time=segment.end_time,
            confidence=confidence,
            audio_duration=segment.duration,
            processing_seconds=finished - started,
            total_latency_seconds=finished - segment.created_at,
        )

    def close(self) -> None:
        model, self._model = self._model, None
        del model

    def _load_model(self, device: Literal["cpu", "cuda"]):
        return self._model_class(
            self.model_size,
            device=device,
            compute_type="float16" if device == "cuda" else "int8",
            cpu_threads=self._cpu_threads,
            download_root=str(self._download_root),
            local_files_only=self._offline,
        )

    def _decode(self, segment: SpeechSegment, language: str) -> list:
        parts, info = self._model.transcribe(
            segment.audio,
            language=None if self._filter_source_language else language,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=False,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )
        if self._filter_source_language and should_reject_language(
            expected=language,
            detected=info.language,
            probability=info.language_probability,
            threshold=self._language_filter_threshold,
        ):
            LOGGER.info(
                "Ignored %s speech while expecting %s (probability %.2f)",
                info.language,
                language,
                info.language_probability,
            )
            return []
        return list(parts)

    def _fallback_to_cpu(self) -> None:
        previous, self._model = self._model, None
        del previous
        self._model = self._load_model("cpu")
        self.device = "cpu"
        LOGGER.info("Whisper %s is ready on CPU int8", self.model_size)

    def _warmup_cuda(self) -> None:
        """Force-load CUDA/cuBLAS/cuDNN before live audio starts."""
        parts, _info = self._model.transcribe(
            np.zeros(1600, dtype=np.float32),
            language="en",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=False,
            no_speech_threshold=0.6,
        )
        list(parts)


def resolve_compute_device(requested: ComputeDevice) -> Literal["cpu", "cuda"]:
    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        return "cuda"
    if requested != "auto":
        raise ValueError(f"Unknown compute device: {requested}")
    try:
        import ctranslate2

        return "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    except (ImportError, RuntimeError, OSError):
        return "cpu"


def should_reject_language(
    *,
    expected: str,
    detected: str,
    probability: float,
    threshold: float,
) -> bool:
    """Reject only confident mismatches so short ambiguous words still pass."""
    return detected != expected and probability >= threshold


def model_is_downloaded(model_size: str, download_root: Path) -> bool:
    """Best-effort local cache check used only for a clear status message."""
    expected_names = {model_size, f"faster-whisper-{model_size}"}
    if not download_root.exists():
        return False
    return any(
        item.is_dir() and any(name in item.name for name in expected_names)
        for item in download_root.iterdir()
    )
