"""Versioned JSON settings used by console prototypes and the future GUI."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppSettings:
    audio_source: str = "system"
    system_device: str = "default"
    microphone_device: str = "default"
    whisper_model: str = "turbo"
    compute_device: str = "auto"
    whisper_cpu_threads: int = 8
    filter_source_language: bool = True
    language_filter_threshold: float = 0.65
    source_language: str = "en"
    target_language: str = "ru"
    translation_model: str = "Helsinki-NLP/opus-mt-en-ru"
    translation_device: str = "auto"
    vad_threshold: float = 0.5
    vad_min_speech_ms: int = 200
    vad_min_silence_ms: int = 350
    vad_max_speech_seconds: float = 10.0
    overlay_x: int = 510
    overlay_y: int = 780
    overlay_width: int = 900
    overlay_height: int = 150
    overlay_font_size: int = 26
    overlay_opacity: float = 0.72
    overlay_max_lines: int = 3
    overlay_show_original: bool = False
    overlay_click_through: bool = True
    minimize_to_tray: bool = True
    hotkey_toggle_translation: str = "Ctrl+Alt+T"
    hotkey_toggle_subtitles: str = "Ctrl+Alt+S"
    hotkey_toggle_overlay_editing: str = "Ctrl+Alt+O"

    @classmethod
    def load(cls, path: Path = Path("config.json")) -> AppSettings:
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read settings from {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Settings in {path} must be a JSON object")
        allowed = {item.name for item in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def save(self, path: Path = Path("config.json")) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def update_from(self, values: dict[str, Any]) -> None:
        allowed = {item.name for item in fields(self)}
        for key, value in values.items():
            if key in allowed and value is not None:
                setattr(self, key, value)
