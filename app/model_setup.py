"""Download and verify the local models required by BellenneRelay."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.config import AppSettings
from app.languages import SUPPORTED_LANGUAGE_PAIRS

WHISPER_REPOSITORIES = {
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}


@dataclass(frozen=True, slots=True)
class ModelRequirement:
    key: str
    title: str
    repository: str
    cache_dir: Path
    required_files: tuple[str, ...]
    alternative_files: tuple[str, ...] = ()
    allow_patterns: tuple[str, ...] = ()


def required_models(settings: AppSettings, models_root: Path) -> list[ModelRequirement]:
    whisper_repository = WHISPER_REPOSITORIES.get(
        settings.whisper_model,
        f"Systran/faster-whisper-{settings.whisper_model}",
    )
    requirements = [
        ModelRequirement(
            key="whisper",
            title=f"Whisper {settings.whisper_model.title()}",
            repository=whisper_repository,
            cache_dir=models_root / "whisper",
            required_files=("config.json", "model.bin", "tokenizer.json"),
            allow_patterns=(
                "config.json",
                "model.bin",
                "tokenizer.json",
                "vocabulary.*",
                "preprocessor_config.json",
            ),
        )
    ]
    for pair in SUPPORTED_LANGUAGE_PAIRS:
        requirements.append(
            ModelRequirement(
                key=pair.key,
                title=f"Translator {pair.source.upper()} → {pair.target.upper()}",
                repository=pair.model_name,
                cache_dir=models_root / "translation",
                required_files=("config.json", "source.spm", "target.spm", "vocab.json"),
                alternative_files=("model.safetensors", "pytorch_model.bin"),
                allow_patterns=(
                    "config.json",
                    "generation_config.json",
                    "model.safetensors",
                    "source.spm",
                    "target.spm",
                    "tokenizer_config.json",
                    "vocab.json",
                ),
            )
        )
    return requirements


def model_is_ready(requirement: ModelRequirement) -> bool:
    snapshots = _snapshot_directories(requirement)
    return any(_snapshot_is_complete(snapshot, requirement) for snapshot in snapshots)


def all_models_ready(requirements: list[ModelRequirement]) -> bool:
    return all(model_is_ready(requirement) for requirement in requirements)


def bundled_models_ready(settings: AppSettings, bundled_root: Path) -> bool:
    """Check materialized model directories included in a distribution."""
    requirements = required_models(settings, bundled_root)
    directories = [bundled_root / "whisper" / settings.whisper_model]
    directories.extend(
        bundled_root / "translation" / requirement.key
        for requirement in requirements[1:]
    )
    return all(
        _snapshot_is_complete(directory, requirement)
        for directory, requirement in zip(directories, requirements, strict=True)
    )


def download_model(requirement: ModelRequirement) -> None:
    from huggingface_hub import snapshot_download
    from huggingface_hub.utils import disable_progress_bars

    # The desktop UI owns progress reporting. Hugging Face's tqdm output expects
    # a console stream, which a PyInstaller windowed executable does not have.
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    disable_progress_bars()
    requirement.cache_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=requirement.repository,
        cache_dir=requirement.cache_dir,
        allow_patterns=list(requirement.allow_patterns),
    )
    if not model_is_ready(requirement):
        raise RuntimeError(f"Downloaded files for {requirement.title} are incomplete")


def _snapshot_directories(requirement: ModelRequirement) -> list[Path]:
    repository_dir = (
        requirement.cache_dir / f"models--{requirement.repository.replace('/', '--')}"
    )
    snapshots_dir = repository_dir / "snapshots"
    if not snapshots_dir.is_dir():
        return []
    return [path for path in snapshots_dir.iterdir() if path.is_dir()]


def _snapshot_is_complete(snapshot: Path, requirement: ModelRequirement) -> bool:
    if not all((snapshot / filename).is_file() for filename in requirement.required_files):
        return False
    if requirement.alternative_files:
        return any((snapshot / filename).is_file() for filename in requirement.alternative_files)
    return True
