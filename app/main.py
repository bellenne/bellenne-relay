"""BellenneRelay desktop entry point."""

from __future__ import annotations

import shutil
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.config import AppSettings
from app.controller import PipelineController
from app.model_setup import all_models_ready, bundled_models_ready, required_models
from app.runtime_paths import (
    RuntimePaths,
    bundled_config_path,
    bundled_models_path,
    runtime_paths,
)
from app.runtime_streams import ensure_standard_streams
from app.ui import MainWindow
from app.ui.model_setup_dialog import ModelSetupDialog
from app.ui.theme import apply_theme
from app.utils.logger import configure_logging


def _load_runtime_settings(paths: RuntimePaths) -> AppSettings:
    paths.root.mkdir(parents=True, exist_ok=True)
    if not paths.config.exists():
        bundled = bundled_config_path()
        if bundled is not None:
            shutil.copy2(bundled, paths.config)
        else:
            AppSettings().save(paths.config)
    return AppSettings.load(paths.config)


def main() -> int:
    ensure_standard_streams()
    paths = runtime_paths()
    configure_logging(paths.logs / "app.log")
    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(False)
    application.setApplicationName("BellenneRelay")
    application.setOrganizationName("Bellenne")
    apply_theme(application)
    settings = _load_runtime_settings(paths)
    requirements = required_models(settings, paths.models)
    bundled_models = bundled_models_path()
    use_bundled_models = bool(
        bundled_models is not None and bundled_models_ready(settings, bundled_models)
    )
    windows: dict[str, object] = {}

    def show_main_window() -> None:
        setup = windows.pop("setup", None)
        if isinstance(setup, ModelSetupDialog):
            setup.hide()
            setup.deleteLater()
        window = MainWindow(
            settings,
            controller=PipelineController(
                paths.models,
                bundled_model_root=bundled_models if use_bundled_models else None,
            ),
            settings_path=paths.config,
        )
        windows["main"] = window
        window.show()

    if use_bundled_models or all_models_ready(requirements):
        show_main_window()
    else:
        setup = ModelSetupDialog(requirements)
        windows["setup"] = setup
        setup.ready.connect(show_main_window)
        setup.show()
        QTimer.singleShot(0, setup.start)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
