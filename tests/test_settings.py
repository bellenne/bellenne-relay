from __future__ import annotations

import json
from pathlib import Path

from app.config import AppSettings


def test_settings_round_trip_unicode_device_name(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    expected = AppSettings(microphone_device="Микрофон (Maono PD200W Mic USB)")

    expected.save(path)
    actual = AppSettings.load(path)

    assert actual == expected
    assert "Микрофон" in path.read_text(encoding="utf-8")


def test_unknown_future_settings_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"whisper_model": "base", "future": True}), encoding="utf-8")

    settings = AppSettings.load(path)

    assert settings.whisper_model == "base"
    assert settings.microphone_device == "default"
    assert (settings.source_language, settings.target_language) == ("en", "ru")
