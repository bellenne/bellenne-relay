"""Errors raised by the audio layer."""


class AudioError(RuntimeError):
    """Base audio error."""


class AudioBackendUnavailable(AudioError):
    """The Windows/PyAudioWPatch backend cannot be initialized."""


class WasapiUnavailable(AudioError):
    """WASAPI is not available on this machine."""


class AudioDeviceNotFound(AudioError):
    """A requested physical or loopback device cannot be found."""


class AudioCaptureError(AudioError):
    """An audio stream failed to start or stopped unexpectedly."""

