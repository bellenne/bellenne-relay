"""BellenneRelay application shell connected to the existing translation pipeline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.config import AppSettings
from app.controller import PipelineController
from app.languages import language_pair, language_pair_from_key
from app.state import ApplicationState
from app.subtitles import SubtitleManager
from app.translation import TranslationResult
from app.ui import theme
from app.ui.hotkeys import GlobalHotkeys
from app.ui.icons import IconProvider
from app.ui.models import HistoryEntry, LogEntry
from app.ui.overlay_window import OverlayWindow
from app.ui.pages import HistoryPage, LogsPage, MainPage, OverlayPage
from app.ui.widgets import SettingsDrawer, StatusIndicator


class MainWindow(QMainWindow):
    NAV_ITEMS = ("Main", "Overlay", "History", "Logs")

    def __init__(
        self,
        settings: AppSettings | None = None,
        controller: PipelineController | None = None,
        settings_path: Path = Path("config.json"),
    ) -> None:
        super().__init__()
        self.settings = settings or AppSettings.load(settings_path)
        self.settings_path = settings_path
        self.controller = controller or PipelineController()
        self._loading_options = True
        self._last_health_error: str | None = None
        self._force_exit = False

        self.overlay = OverlayWindow(self.settings)
        self.subtitle_manager = SubtitleManager(
            self.overlay,
            max_lines=self.settings.overlay_max_lines,
            show_original=self.settings.overlay_show_original,
        )
        self.hotkeys = GlobalHotkeys()

        self.setWindowTitle("BellenneRelay — Real-time Translation")
        self.setWindowIcon(IconProvider.product())
        self.setMinimumSize(860, 580)
        self.resize(1180, 760)
        self._build_ui()
        self._build_tray()
        self._connect_signals()
        self._load_settings_into_ui()
        self._loading_options = False
        self._apply_overlay_options()
        self._apply_state(ApplicationState.STOPPED.value)
        self.controller.refresh_devices()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_runtime)
        self._timer.start(50)
        self.hotkeys.start()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_navigation())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        self.pages = QStackedWidget()
        self.main_page = MainPage()
        self.overlay_page = OverlayPage()
        self.history_page = HistoryPage()
        self.logs_page = LogsPage()
        for page in (
            self.main_page,
            self.overlay_page,
            self.history_page,
            self.logs_page,
        ):
            self.pages.addWidget(page)
        self.settings_drawer = SettingsDrawer()
        body_layout.addWidget(self.pages, 1)
        body_layout.addWidget(self.settings_drawer)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        # Preserve original control names for small existing integrations.
        self.mode_combo = self.settings_drawer.mode_combo
        self.system_combo = self.settings_drawer.system_combo
        self.microphone_combo = self.settings_drawer.microphone_combo
        self.model_combo = self.settings_drawer.model_combo
        self.compute_combo = self.settings_drawer.compute_combo
        self.language_combo = self.settings_drawer.language_combo
        self.language_filter_check = self.settings_drawer.language_filter_check
        self.refresh_button = self.settings_drawer.refresh_button
        self.start_stop_button = self.main_page.start_stop_button
        self.system_level = self.main_page.system_meter.meter
        self.microphone_level = self.main_page.microphone_meter.meter
        self.history = self.history_page.table
        self.overlay_font_spin = self.overlay_page.font_spin
        self.overlay_opacity_slider = self.overlay_page.opacity_slider
        self.overlay_lines_spin = self.overlay_page.lines_spin
        self.overlay_original_check = self.overlay_page.original_check
        self.overlay_click_check = self.overlay_page.click_check
        self.overlay_show_button = self.overlay_page.show_button
        self.overlay_edit_button = self.overlay_page.edit_button
        self.overlay_reset_button = self.overlay_page.reset_button

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 16, 10)
        layout.setSpacing(12)
        product_icon = QLabel()
        product_icon.setPixmap(IconProvider.product().pixmap(28, 28))
        product_icon.setFixedSize(32, 32)
        identity = QVBoxLayout()
        identity.setSpacing(0)
        name = QLabel("BellenneRelay")
        name.setObjectName("ProductName")
        subtitle = QLabel("Real-time translation")
        subtitle.setObjectName("ProductSubtitle")
        identity.addWidget(name)
        identity.addWidget(subtitle)
        layout.addWidget(product_icon)
        layout.addLayout(identity)
        layout.addStretch()
        self.status_indicator = StatusIndicator("Ready")
        layout.addWidget(self.status_indicator)
        self.settings_button = QToolButton()
        self.settings_button.setIcon(IconProvider.settings())
        self.settings_button.setToolTip("Settings")
        self.settings_button.setAccessibleName("Settings")
        layout.addWidget(self.settings_button)
        return header

    def _build_navigation(self) -> QWidget:
        navigation = QFrame()
        navigation.setObjectName("Navigation")
        layout = QHBoxLayout(navigation)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)
        self.nav_buttons: list[QPushButton] = []
        icon_factories = (
            IconProvider.main,
            IconProvider.overlay,
            IconProvider.history,
            IconProvider.logs,
        )
        for index, (label, icon_factory) in enumerate(
            zip(self.NAV_ITEMS, icon_factories, strict=True)
        ):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setIcon(icon_factory(index == 0))
            button.setProperty("active", index == 0)
            button.clicked.connect(lambda checked=False, page=index: self._select_page(page))
            self.nav_buttons.append(button)
            layout.addWidget(button)
        layout.addStretch()
        return navigation

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        menu = QMenu()
        open_action = QAction("Open BellenneRelay", self)
        self.tray_start_action = QAction("Start translation", self)
        self.tray_stop_action = QAction("Stop translation", self)
        show_subtitles_action = QAction("Show overlay", self)
        hide_subtitles_action = QAction("Hide overlay", self)
        exit_action = QAction("Exit", self)
        open_action.triggered.connect(self._open_from_tray)
        self.tray_start_action.triggered.connect(self._start_from_tray)
        self.tray_stop_action.triggered.connect(self.controller.stop)
        show_subtitles_action.triggered.connect(self.overlay.show)
        hide_subtitles_action.triggered.connect(self.overlay.hide)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(self.tray_start_action)
        menu.addAction(self.tray_stop_action)
        menu.addSeparator()
        menu.addAction(show_subtitles_action)
        menu.addAction(hide_subtitles_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("BellenneRelay")
        self.tray.activated.connect(self._tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def _connect_signals(self) -> None:
        self.settings_button.clicked.connect(self.settings_drawer.toggle)
        self.settings_drawer.close_requested.connect(
            lambda: self.settings_drawer.set_open(False)
        )
        self.settings_drawer.refresh_requested.connect(self.controller.refresh_devices)
        self.start_stop_button.clicked.connect(self._toggle_translation)
        self.main_page.overlay_requested.connect(self._toggle_overlay)
        self.mode_combo.currentIndexChanged.connect(self._update_mode_controls)
        self.language_combo.currentIndexChanged.connect(self._update_language_direction)
        self.controller.state_changed.connect(self._apply_state)
        self.controller.devices_ready.connect(self._populate_devices)
        self.controller.translation_ready.connect(self._add_translation)
        self.controller.component_changed.connect(self._component_changed)
        self.controller.error_occurred.connect(self._show_error)
        self.hotkeys.toggle_translation.connect(self._toggle_translation)
        self.hotkeys.toggle_subtitles.connect(self._toggle_overlay)
        self.hotkeys.toggle_overlay_editing.connect(self._hotkey_toggle_editing)
        self.hotkeys.registration_error.connect(
            lambda message: self._log("WARNING", "Hotkeys", message)
        )
        self.overlay_font_spin.valueChanged.connect(self._apply_overlay_options)
        self.overlay_opacity_slider.valueChanged.connect(self._apply_overlay_options)
        self.overlay_lines_spin.valueChanged.connect(self._apply_overlay_options)
        self.overlay_original_check.toggled.connect(self._apply_overlay_options)
        self.overlay_click_check.toggled.connect(self._apply_overlay_options)
        self.overlay_show_button.clicked.connect(self._toggle_overlay)
        self.overlay_edit_button.toggled.connect(self._toggle_overlay_editing)
        self.overlay_reset_button.clicked.connect(self._reset_overlay_position)

    def _load_settings_into_ui(self) -> None:
        self._select_data(self.mode_combo, self.settings.audio_source)
        self._select_data(self.model_combo, self.settings.whisper_model)
        self._select_data(self.compute_combo, self.settings.compute_device)
        self._select_data(
            self.language_combo,
            f"{self.settings.source_language}-{self.settings.target_language}",
        )
        self.language_filter_check.setChecked(self.settings.filter_source_language)
        self.overlay_font_spin.setValue(self.settings.overlay_font_size)
        self.overlay_opacity_slider.setValue(round(self.settings.overlay_opacity * 100))
        self.overlay_lines_spin.setValue(self.settings.overlay_max_lines)
        self.overlay_original_check.setChecked(self.settings.overlay_show_original)
        self.overlay_click_check.setChecked(self.settings.overlay_click_through)
        self._update_mode_controls()
        self._update_language_direction()

    def _populate_devices(self, outputs: list, microphones: list) -> None:
        self._fill_device_combo(
            self.system_combo,
            "Default output device",
            outputs,
            self.settings.system_device,
        )
        self._fill_device_combo(
            self.microphone_combo,
            "Default microphone",
            microphones,
            self.settings.microphone_device,
        )
        self._log(
            "INFO",
            "Audio",
            f"Devices refreshed: {len(outputs)} outputs, {len(microphones)} microphones",
        )

    @staticmethod
    def _fill_device_combo(combo, default_label, devices, selected) -> None:
        combo.clear()
        combo.addItem(default_label, "default")
        selected_index = 0
        for device in devices:
            label = device.name + (" [Windows default]" if device.is_default else "")
            combo.addItem(label, device.name)
            if selected.casefold() in device.name.casefold():
                selected_index = combo.count() - 1
        combo.setCurrentIndex(selected_index)

    @staticmethod
    def _select_data(combo, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        icon_factories = (
            IconProvider.main,
            IconProvider.overlay,
            IconProvider.history,
            IconProvider.logs,
        )
        for button_index, button in enumerate(self.nav_buttons):
            active = button_index == index
            button.setProperty("active", active)
            button.setIcon(icon_factories[button_index](active))
            button.style().unpolish(button)
            button.style().polish(button)

    def _toggle_translation(self) -> None:
        if self.controller.state in (ApplicationState.STOPPED, ApplicationState.ERROR):
            system_device = (
                self.system_combo.currentData()
                if self.system_combo.count()
                else self.settings.system_device
            )
            microphone_device = (
                self.microphone_combo.currentData()
                if self.microphone_combo.count()
                else self.settings.microphone_device
            )
            pair = language_pair_from_key(self.language_combo.currentData())
            self.settings.update_from(
                {
                    "audio_source": self.mode_combo.currentData(),
                    "system_device": system_device,
                    "microphone_device": microphone_device,
                    "whisper_model": self.model_combo.currentData(),
                    "compute_device": self.compute_combo.currentData(),
                    "source_language": pair.source,
                    "target_language": pair.target,
                    "translation_model": pair.model_name,
                    "filter_source_language": self.language_filter_check.isChecked(),
                }
            )
            self.settings.save(self.settings_path)
            self._last_health_error = None
            self.controller.start(self.settings)
        else:
            self.controller.stop()

    def _apply_state(self, state: str) -> None:
        running = state in {
            ApplicationState.INITIALIZING.value,
            ApplicationState.RUNNING.value,
            ApplicationState.STOPPING.value,
        }
        status_map = {
            ApplicationState.STOPPED.value: ("Ready", theme.SUCCESS, "Ready to translate"),
            ApplicationState.INITIALIZING.value: (
                "Starting…",
                theme.WARNING,
                "Loading speech and translation models…",
            ),
            ApplicationState.RUNNING.value: (
                "Listening",
                theme.SUCCESS,
                "Listening for speech…",
            ),
            ApplicationState.STOPPING.value: ("Stopping…", theme.WARNING, "Stopping…"),
            ApplicationState.ERROR.value: ("Error", theme.DANGER, "Translation stopped"),
        }
        status_text, color, speech_text = status_map.get(
            state, (state.title(), theme.TEXT_MUTED, state.title())
        )
        self.status_indicator.set_status(status_text, color)
        self.main_page.transcript.set_speech_state(speech_text)
        self.start_stop_button.set_running(running)
        self.start_stop_button.setEnabled(state != ApplicationState.STOPPING.value)
        self.tray_start_action.setEnabled(not running)
        self.tray_stop_action.setEnabled(running)
        self.settings_drawer.set_controls_enabled(not running)
        self._log("INFO", "Application", f"State changed to {state}")

    def _component_changed(self, component: str, status: str) -> None:
        self.settings_drawer.set_component_status(component, status)
        self._log("INFO", component.title(), status.title())

    def _add_translation(self, result: TranslationResult) -> None:
        self.subtitle_manager.show(result)
        now = datetime.now().strftime("%H:%M:%S")
        latency_ms = round(result.total_latency_seconds * 1000)
        self.main_page.transcript.add_entry(
            now,
            result.source_id,
            result.original,
            result.translated,
        )
        self.history_page.add_entry(
            HistoryEntry(
                now,
                result.source_id,
                self._selected_language_pair().label,
                result.original,
                result.translated,
                latency_ms,
            )
        )
        self.main_page.set_latency(latency_ms)
        self.main_page.transcript.set_speech_state("Listening for speech…")
        self.overlay_page.update_preview(result.original, result.translated)
        self._log(
            "INFO",
            "Translation",
            f"{result.source_id}: STT {result.transcription_seconds * 1000:.0f} ms, "
            f"translation {result.translation_seconds * 1000:.0f} ms, total {latency_ms} ms",
        )

    def _poll_runtime(self) -> None:
        levels = self.controller.levels()
        self.system_level.set_level(levels.get("system", -96.0))
        self.microphone_level.set_level(levels.get("microphone", -96.0))
        error = self.controller.health_error()
        if error and error != self._last_health_error:
            self._last_health_error = error
            self._show_error(error)
            self.controller.stop()

    def _update_mode_controls(self) -> None:
        self.settings_drawer.update_source_visibility()
        labels = {
            "system": "System Audio",
            "microphone": "Microphone",
            "both": "System + Mic",
        }
        self.main_page.set_source(labels.get(self.mode_combo.currentData(), "System Audio"))

    def _selected_language_pair(self):
        key = self.language_combo.currentData()
        if key:
            return language_pair_from_key(key)
        return language_pair(self.settings.source_language, self.settings.target_language)

    def _update_language_direction(self) -> None:
        pair = self._selected_language_pair()
        previous = getattr(self, "_current_language_direction", None)
        if previous is not None and previous != pair.key and not self._loading_options:
            self.main_page.transcript.clear()
            self.main_page.set_latency(None)
            self.subtitle_manager.clear()
        self._current_language_direction = pair.key
        self.settings.source_language = pair.source
        self.settings.target_language = pair.target
        self.settings.translation_model = pair.model_name
        self.main_page.set_language(pair.source_name, pair.target_name)
        self.main_page.transcript.set_languages(
            pair.source,
            pair.source_name,
            pair.target,
            pair.target_name,
        )
        self.overlay_page.set_languages(pair.source_name, pair.target_name)

    def _apply_overlay_options(self) -> None:
        if self._loading_options:
            return
        self.settings.overlay_font_size = self.overlay_font_spin.value()
        self.settings.overlay_opacity = self.overlay_opacity_slider.value() / 100
        self.settings.overlay_max_lines = self.overlay_lines_spin.value()
        self.settings.overlay_show_original = self.overlay_original_check.isChecked()
        self.settings.overlay_click_through = self.overlay_click_check.isChecked()
        self.overlay.apply_style(self.settings.overlay_font_size, self.settings.overlay_opacity)
        self.overlay.set_click_through(self.settings.overlay_click_through)
        self.subtitle_manager.update_options(
            max_lines=self.settings.overlay_max_lines,
            show_original=self.settings.overlay_show_original,
        )
        self.overlay_page.apply_preview_options(
            self.settings.overlay_font_size,
            self.settings.overlay_opacity,
            self.settings.overlay_show_original,
        )

    def _toggle_overlay(self) -> None:
        self.overlay.setVisible(not self.overlay.isVisible())

    def _toggle_overlay_editing(self, enabled: bool) -> None:
        self.overlay.set_editing(enabled)
        if enabled:
            self.overlay.show()

    def _hotkey_toggle_editing(self) -> None:
        self.overlay_edit_button.toggle()

    def _open_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _start_from_tray(self) -> None:
        if self.controller.state in (ApplicationState.STOPPED, ApplicationState.ERROR):
            self._toggle_translation()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._open_from_tray()

    def exit_application(self) -> None:
        self._force_exit = True
        self.close()
        application = QApplication.instance()
        if application is not None:
            application.quit()

    def _reset_overlay_position(self) -> None:
        self.overlay.place_bottom_center()
        self.overlay.show()

    def _show_error(self, message: str) -> None:
        self._log("ERROR", "Application", message)
        QMessageBox.critical(self, "BellenneRelay", message)

    def _log(self, level: str, component: str, message: str) -> None:
        self.logs_page.add_entry(
            LogEntry(datetime.now().strftime("%H:%M:%S"), level, component, message)
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt API)
        if event.key() == Qt.Key_Escape and self.settings_drawer.is_open:
            self.settings_drawer.set_open(False)
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt API)
        if (
            not self._force_exit
            and event.spontaneous()
            and self.settings.minimize_to_tray
            and QSystemTrayIcon.isSystemTrayAvailable()
        ):
            self.hide()
            event.ignore()
            return
        self._timer.stop()
        self.hotkeys.stop()
        self.controller.shutdown()
        geometry = self.overlay.geometry()
        self.settings.overlay_x = geometry.x()
        self.settings.overlay_y = geometry.y()
        self.settings.overlay_width = geometry.width()
        self.settings.overlay_height = geometry.height()
        self.overlay.close()
        self.tray.hide()
        self.settings.save(self.settings_path)
        event.accept()
