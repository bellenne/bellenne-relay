from __future__ import annotations

import pytest

from app.audio.devices import AudioDeviceManager, AudioDeviceType
from app.audio.errors import AudioDeviceNotFound


class FakeAudio:
    DEVICES = [
        {
            "index": 2,
            "name": "Speakers (USB DAC)",
            "maxInputChannels": 0,
            "maxOutputChannels": 2,
            "defaultSampleRate": 48000.0,
            "isLoopbackDevice": False,
        },
        {
            "index": 3,
            "name": "Microphone (USB)",
            "maxInputChannels": 1,
            "maxOutputChannels": 0,
            "defaultSampleRate": 44100.0,
            "isLoopbackDevice": False,
        },
        {
            "index": 8,
            "name": "Speakers (USB DAC) [Loopback]",
            "maxInputChannels": 2,
            "maxOutputChannels": 0,
            "defaultSampleRate": 48000.0,
            "isLoopbackDevice": True,
        },
    ]

    def get_host_api_info_by_type(self, api_type: int):
        assert api_type == 13
        return {
            "index": 1,
            "deviceCount": len(self.DEVICES),
            "baseDeviceIndex": 2,
            "defaultOutputDevice": 2,
            "defaultInputDevice": 3,
        }

    def get_device_info_generator_by_host_api(self, *, host_api_index: int):
        assert host_api_index == 1
        yield from self.DEVICES

    def get_wasapi_loopback_analogue_by_dict(self, physical: dict):
        if physical["index"] == 2:
            return self.DEVICES[2]
        raise LookupError


def test_lists_physical_output_but_captures_its_loopback() -> None:
    manager = AudioDeviceManager(FakeAudio(), 13)

    devices = manager.list_system_outputs()

    assert len(devices) == 1
    assert devices[0].name == "Speakers (USB DAC)"
    assert devices[0].physical_index == 2
    assert devices[0].capture_index == 8
    assert devices[0].is_default


def test_lists_microphone_without_loopback_duplicates() -> None:
    manager = AudioDeviceManager(FakeAudio(), 13)

    devices = manager.list_microphones()

    assert [(device.name, device.capture_index) for device in devices] == [
        ("Microphone (USB)", 3)
    ]
    assert manager.resolve(AudioDeviceType.MICROPHONE, "default") == devices[0]


def test_resolve_rejects_missing_physical_index() -> None:
    manager = AudioDeviceManager(FakeAudio(), 13)

    with pytest.raises(AudioDeviceNotFound):
        manager.resolve(AudioDeviceType.SYSTEM, "999")


def test_resolve_by_stable_partial_name() -> None:
    manager = AudioDeviceManager(FakeAudio(), 13)

    device = manager.resolve(AudioDeviceType.MICROPHONE, "USB")

    assert device.physical_index == 3
