from __future__ import annotations

import time

import numpy as np

from app.speech.engine import SpeechRecognitionEngine
from app.speech.models import SpeechSegment, TranscriptionResult
from app.speech.worker import TranscriptionWorker


class FakeEngine(SpeechRecognitionEngine):
    def transcribe(self, segment: SpeechSegment, language: str = "en") -> TranscriptionResult:
        return TranscriptionResult(
            text=language,
            source_id=segment.source_id,
            start_time=segment.start_time,
            end_time=segment.end_time,
            confidence=1.0,
            audio_duration=segment.duration,
            processing_seconds=0.0,
            total_latency_seconds=0.0,
        )

    def close(self) -> None:
        pass


def make_segment(source: str) -> SpeechSegment:
    now = time.monotonic()
    return SpeechSegment(
        audio=np.zeros(1600, dtype=np.float32),
        source_id=source,
        start_time=now,
        end_time=now + 0.1,
        created_at=now,
    )


def test_bounded_queue_discards_oldest_segment() -> None:
    worker = TranscriptionWorker(FakeEngine, lambda result: None, queue_size=1)

    worker.submit(make_segment("OLD"))
    worker.submit(make_segment("LIVE"))

    assert worker.dropped_segments == 1
    assert worker._queue.get_nowait().source_id == "LIVE"


def test_worker_processes_segment_and_stops_cleanly() -> None:
    results: list[TranscriptionResult] = []
    worker = TranscriptionWorker(FakeEngine, results.append)
    worker.start()
    assert worker.wait_ready(timeout=1)

    worker.submit(make_segment("SYSTEM"))
    worker.stop()

    assert [result.source_id for result in results] == ["SYSTEM"]
    assert worker.error is None
