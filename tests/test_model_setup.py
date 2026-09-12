from __future__ import annotations

from pathlib import Path

from app.config import AppSettings
from app.model_setup import (
    ModelRequirement,
    all_models_ready,
    bundled_models_ready,
    model_is_ready,
    required_models,
)
from app.runtime_paths import runtime_paths


def requirement(cache_dir: Path) -> ModelRequirement:
    return ModelRequirement(
        key="test",
        title="Test model",
        repository="owner/model",
        cache_dir=cache_dir,
        required_files=("config.json", "tokenizer.json"),
        alternative_files=("model.safetensors", "pytorch_model.bin"),
    )


def test_model_is_ready_only_for_complete_snapshot(tmp_path: Path) -> None:
    model = requirement(tmp_path)
    snapshot = tmp_path / "models--owner--model" / "snapshots" / "revision"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").touch()
    (snapshot / "tokenizer.json").touch()

    assert not model_is_ready(model)

    (snapshot / "model.safetensors").touch()

    assert model_is_ready(model)
    assert all_models_ready([model])


def test_runtime_path_override_is_independent_of_working_directory(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "Bellenne data"
    monkeypatch.setenv("BELLENNE_RELAY_HOME", str(data_root))

    paths = runtime_paths()

    assert paths.root == data_root.resolve()
    assert paths.config == data_root.resolve() / "config.json"
    assert paths.models == data_root.resolve() / "models"


def test_turbo_uses_available_faster_whisper_repository(tmp_path: Path) -> None:
    requirement = required_models(AppSettings(whisper_model="turbo"), tmp_path)[0]

    assert requirement.repository == "mobiuslabsgmbh/faster-whisper-large-v3-turbo"


def test_materialized_bundled_models_are_detected(tmp_path: Path) -> None:
    settings = AppSettings(whisper_model="turbo")
    requirements = required_models(settings, tmp_path)
    directories = [tmp_path / "whisper" / "turbo"]
    directories.extend(tmp_path / "translation" / item.key for item in requirements[1:])
    for directory, item in zip(directories, requirements, strict=True):
        directory.mkdir(parents=True)
        for filename in item.required_files:
            (directory / filename).touch()
        if item.alternative_files:
            (directory / item.alternative_files[0]).touch()

    assert bundled_models_ready(settings, tmp_path)

    (tmp_path / "translation" / "ru-en" / "config.json").unlink()

    assert not bundled_models_ready(settings, tmp_path)
