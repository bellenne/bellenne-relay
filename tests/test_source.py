from __future__ import annotations

import time
import wave
from pathlib import Path

from app.audio.devices import AudioDevice, AudioDeviceType
from app.audio.source import AudioCaptureSource, AudioSourceState


class FakeModule:
    paInt16 = 8
    paContinue = 0


class FakeStream:
    def __init__(self, callback):
        self.callback = callback
        self.active = False

    def start_stream(self):
        self.active = True
        self.callback(b"\x00\x40" * 8, 8, {}, 0)

    def is_active(self):
        return self.active

    def stop_stream(self):
        self.active = False

    def close(self):
        pass


class FakeAudio:
    def open(self, **kwargs):
        assert kwargs["input"] is True
        assert kwargs["start"] is False
        return FakeStream(kwargs["stream_callback"])

    def get_sample_size(self, audio_format):
        assert audio_format == FakeModule.paInt16
        return 2


def test_source_writes_callback_data_to_wav(tmp_path: Path) -> None:
    device = AudioDevice(
        id="microphone:3",
        name="Test microphone",
        kind=AudioDeviceType.MICROPHONE,
        capture_index=3,
        physical_index=3,
        channels=1,
        sample_rate=16000,
    )
    path = tmp_path / "capture.wav"
    source = AudioCaptureSource(FakeAudio(), FakeModule(), device, path)

    source.start()
    time.sleep(0.15)
    source.stop()

    assert source.state is AudioSourceState.STOPPED
    assert source.stats().frames_written == 8
    with wave.open(str(path), "rb") as captured:
        assert captured.getnchannels() == 1
        assert captured.getframerate() == 16000
        assert captured.getnframes() == 8

