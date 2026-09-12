from __future__ import annotations

import sys

from app.runtime_paths import bundled_models_path


def test_frozen_build_finds_models_beside_executable(tmp_path, monkeypatch) -> None:
    executable = tmp_path / "BellenneRelay.exe"
    executable.touch()
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))

    assert bundled_models_path() == models
