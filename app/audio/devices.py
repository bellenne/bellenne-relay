"""User-facing WASAPI output and microphone discovery."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .errors import AudioDeviceNotFound, WasapiUnavailable


class AudioDeviceType(StrEnum):
    SYSTEM = "system"
    MICROPHONE = "microphone"


@dataclass(frozen=True, slots=True)
class AudioDevice:
    """A capture-ready endpoint displayed as a friendly physical device."""

    id: str
    name: str
    kind: AudioDeviceType
    capture_index: int
    physical_index: int
    channels: int
    sample_rate: int
    is_default: bool = False


class AudioDeviceManager:
    """Resolve physical WASAPI endpoints to their capture endpoints."""

    def __init__(self, audio: Any, wasapi_type: int) -> None:
        self._audio = audio
        self._wasapi_type = wasapi_type

    def _wasapi_info(self) -> Mapping[str, Any]:
        try:
            return self._audio.get_host_api_info_by_type(self._wasapi_type)
        except OSError as exc:
            raise WasapiUnavailable("Windows WASAPI host API was not found.") from exc

    def _wasapi_devices(self) -> list[Mapping[str, Any]]:
        info = self._wasapi_info()
        host_index = int(info["index"])
        generator = getattr(self._audio, "get_device_info_generator_by_host_api", None)
        if generator is not None:
            return list(generator(host_api_index=host_index))

        first = int(info.get("baseDeviceIndex", 0))
        count = int(info["deviceCount"])
        return [self._audio.get_device_info_by_index(i) for i in range(first, first + count)]

    def list_system_outputs(self) -> list[AudioDevice]:
        """Return physical output endpoints with a working loopback analogue."""
        info = self._wasapi_info()
        default_index = int(info.get("defaultOutputDevice", -1))
        result: list[AudioDevice] = []

        for physical in self._wasapi_devices():
            if physical.get("isLoopbackDevice") or int(physical.get("maxOutputChannels", 0)) <= 0:
                continue
            try:
                loopback = self._loopback_for(physical)
            except AudioDeviceNotFound:
                continue
            physical_index = int(physical["index"])
            result.append(
                AudioDevice(
                    id=f"system:{physical_index}",
                    name=str(physical["name"]),
                    kind=AudioDeviceType.SYSTEM,
                    capture_index=int(loopback["index"]),
                    physical_index=physical_index,
                    channels=max(1, int(loopback["maxInputChannels"])),
                    sample_rate=round(float(loopback["defaultSampleRate"])),
                    is_default=physical_index == default_index,
                )
            )
        return _unique_by_name(result)

    def list_microphones(self) -> list[AudioDevice]:
        """Return real WASAPI input endpoints, excluding loopback devices."""
        info = self._wasapi_info()
        default_index = int(info.get("defaultInputDevice", -1))
        result: list[AudioDevice] = []

        for item in self._wasapi_devices():
            if item.get("isLoopbackDevice") or int(item.get("maxInputChannels", 0)) <= 0:
                continue
            index = int(item["index"])
            result.append(
                AudioDevice(
                    id=f"microphone:{index}",
                    name=str(item["name"]),
                    kind=AudioDeviceType.MICROPHONE,
                    capture_index=index,
                    physical_index=index,
                    channels=max(1, int(item["maxInputChannels"])),
                    sample_rate=round(float(item["defaultSampleRate"])),
                    is_default=index == default_index,
                )
            )
        return _unique_by_name(result)

    def default_system_output(self) -> AudioDevice:
        default = next((device for device in self.list_system_outputs() if device.is_default), None)
        if default is None:
            raise AudioDeviceNotFound("Default WASAPI output has no loopback endpoint.")
        return default

    def default_microphone(self) -> AudioDevice:
        default = next((device for device in self.list_microphones() if device.is_default), None)
        if default is None:
            raise AudioDeviceNotFound("Default WASAPI microphone was not found.")
        return default

    def resolve(self, kind: AudioDeviceType, selector: str) -> AudioDevice:
        devices = (
            self.list_system_outputs()
            if kind is AudioDeviceType.SYSTEM
            else self.list_microphones()
        )
        if selector.casefold() == "default":
            default = next((device for device in devices if device.is_default), None)
            if default is None:
                raise AudioDeviceNotFound(f"Default {kind.value} device was not found.")
            return default

        try:
            physical_index = int(selector)
        except ValueError:
            name_matches = [
                item for item in devices if selector.casefold() in item.name.casefold()
            ]
            if len(name_matches) == 1:
                return name_matches[0]
            if len(name_matches) > 1:
                names = ", ".join(item.name for item in name_matches)
                raise AudioDeviceNotFound(
                    f"Device name {selector!r} is ambiguous; matches: {names}."
                ) from None
            raise AudioDeviceNotFound(
                f"{kind.value.title()} device named {selector!r} was not found."
            ) from None
        else:
            device = next(
                (item for item in devices if item.physical_index == physical_index), None
            )
            if device is None:
                raise AudioDeviceNotFound(
                    f"{kind.value.title()} device {physical_index} was not found."
                )
            return device

    def _loopback_for(self, physical: Mapping[str, Any]) -> Mapping[str, Any]:
        resolver = getattr(self._audio, "get_wasapi_loopback_analogue_by_dict", None)
        if resolver is not None:
            try:
                return resolver(dict(physical))
            except LookupError:
                pass

        physical_name = str(physical["name"]).casefold()
        candidates: Iterable[Mapping[str, Any]] = self._audio.get_loopback_device_info_generator()
        match = next(
            (item for item in candidates if physical_name in str(item["name"]).casefold()),
            None,
        )
        if match is None:
            raise AudioDeviceNotFound(
                f"No WASAPI Loopback endpoint corresponds to {physical['name']!r}."
            )
        return match


def _unique_by_name(devices: Iterable[AudioDevice]) -> list[AudioDevice]:
    """Hide duplicate PortAudio endpoints while preserving a default endpoint."""
    result: dict[str, AudioDevice] = {}
    for device in devices:
        key = device.name.casefold()
        previous = result.get(key)
        if previous is None or device.is_default:
            result[key] = device
    return list(result.values())
