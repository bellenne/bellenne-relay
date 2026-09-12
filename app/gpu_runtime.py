"""Make bundled NVIDIA runtime libraries discoverable on Windows."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_DLL_DIRECTORY_HANDLES: list[object] = []


def configure_gpu_dll_search() -> None:
    """Register CUDA DLL folders before CTranslate2 is imported."""
    if os.name != "nt":
        return

    candidates: list[Path] = []
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        candidates.append(Path(frozen_root))

    for package in ("nvidia.cublas", "nvidia.cudnn"):
        spec = importlib.util.find_spec(package)
        if spec is None or spec.submodule_search_locations is None:
            continue
        candidates.extend(Path(location) / "bin" for location in spec.submodule_search_locations)

    current_path = os.environ.get("PATH", "")
    known = {item.casefold() for item in current_path.split(os.pathsep) if item}
    for directory in candidates:
        if not directory.is_dir() or str(directory).casefold() in known:
            continue
        _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(directory)))
        current_path = f"{directory}{os.pathsep}{current_path}"
        known.add(str(directory).casefold())
    os.environ["PATH"] = current_path
