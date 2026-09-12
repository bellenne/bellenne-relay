"""Stable writable paths for development and frozen application builds."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    root: Path
    config: Path
    models: Path
    logs: Path


def runtime_paths() -> RuntimePaths:
    """Resolve paths independently of the process working directory."""
    override = os.environ.get("BELLENNE_RELAY_HOME")
    if override:
        root = Path(override).expanduser().resolve()
    elif getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            root = Path(local_app_data) / "BellenneRelay"
        else:
            root = Path(sys.executable).resolve().parent / "data"
    else:
        root = Path(__file__).resolve().parents[1]
    return RuntimePaths(
        root=root,
        config=root / "config.json",
        models=root / "models",
        logs=root / "logs",
    )


def bundled_config_path() -> Path | None:
    """Return the config template shipped beside the frozen executable."""
    if not getattr(sys, "frozen", False):
        return None
    candidate = Path(sys.executable).resolve().parent / "config.json"
    return candidate if candidate.is_file() else None


def bundled_models_path() -> Path | None:
    """Return packaged models in a build or versioned model assets in development."""
    if getattr(sys, "frozen", False):
        candidate = Path(sys.executable).resolve().parent / "models"
    else:
        candidate = Path(__file__).resolve().parents[1] / "model_assets"
    return candidate if candidate.is_dir() else None
