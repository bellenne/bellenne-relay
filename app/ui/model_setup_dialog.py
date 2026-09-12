"""First-run model download UI."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.model_setup import ModelRequirement, download_model, model_is_ready
from app.ui import theme
from app.ui.icons import IconProvider


class ModelDownloadWorker(QObject):
    model_status = Signal(str, str)
    overall_progress = Signal(int, int, str)
    finished = Signal(bool, str)

    def __init__(self, requirements: list[ModelRequirement]) -> None:
        super().__init__()
        self.requirements = requirements

    @Slot()
    def run(self) -> None:
        total = len(self.requirements)
        try:
            for index, requirement in enumerate(self.requirements):
                self.overall_progress.emit(index, total, requirement.title)
                if model_is_ready(requirement):
                    self.model_status.emit(requirement.key, "Ready")
                else:
                    self.model_status.emit(requirement.key, "Downloading…")
                    download_model(requirement)
                    self.model_status.emit(requirement.key, "Ready")
                self.overall_progress.emit(index + 1, total, requirement.title)
        except Exception as exc:
            self.finished.emit(False, str(exc))
            return
        self.finished.emit(True, "")


class ModelSetupDialog(QDialog):
    ready = Signal()

    def __init__(
        self,
        requirements: list[ModelRequirement],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.requirements = requirements
        self._thread: QThread | None = None
        self._worker: ModelDownloadWorker | None = None
        self._worker_result: tuple[bool, str] | None = None
        self.setWindowTitle("BellenneRelay — Model setup")
        self.setWindowIcon(IconProvider.product())
        self.setMinimumSize(580, 430)
        self.resize(620, 470)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        identity = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(IconProvider.product().pixmap(36, 36))
        icon.setFixedSize(40, 40)
        names = QVBoxLayout()
        names.setSpacing(1)
        product = QLabel("BellenneRelay")
        product.setObjectName("ProductName")
        subtitle = QLabel("Preparing local translation models")
        subtitle.setObjectName("ProductSubtitle")
        names.addWidget(product)
        names.addWidget(subtitle)
        identity.addWidget(icon)
        identity.addLayout(names)
        identity.addStretch()
        root.addLayout(identity)

        heading = QLabel("One-time model setup")
        heading.setObjectName("PanelTitle")
        explanation = QLabel(
            "BellenneRelay downloads the speech model and both translation directions. "
            "They are stored locally and future launches work offline."
        )
        explanation.setObjectName("MutedLabel")
        explanation.setWordWrap(True)
        root.addWidget(heading)
        root.addWidget(explanation)

        models_panel = QFrame()
        models_panel.setObjectName("Panel")
        models_layout = QVBoxLayout(models_panel)
        models_layout.setContentsMargins(16, 12, 16, 12)
        models_layout.setSpacing(0)
        self.status_labels: dict[str, QLabel] = {}
        for requirement in self.requirements:
            row = QHBoxLayout()
            row.setContentsMargins(4, 8, 4, 8)
            name = QLabel(requirement.title)
            status = QLabel("Waiting")
            status.setObjectName("TechnicalValue")
            status.setAlignment(status.alignment())
            self.status_labels[requirement.key] = status
            row.addWidget(name)
            row.addStretch()
            row.addWidget(status)
            models_layout.addLayout(row)
        root.addWidget(models_panel)

        self.current_label = QLabel("Checking local models…")
        self.current_label.setObjectName("MutedLabel")
        root.addWidget(self.current_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, len(self.requirements))
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        root.addWidget(self.progress)
        self.activity = QProgressBar()
        self.activity.setRange(0, 0)
        self.activity.setTextVisible(False)
        root.addWidget(self.activity)

        buttons = QHBoxLayout()
        self.error_label = QLabel()
        self.error_label.setObjectName("SetupError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        self.retry_button = QPushButton("Retry")
        self.retry_button.clicked.connect(self.start)
        self.retry_button.hide()
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self._exit_application)
        self.exit_button.hide()
        buttons.addWidget(self.error_label, 1)
        buttons.addWidget(self.exit_button)
        buttons.addWidget(self.retry_button)
        root.addLayout(buttons)

    def start(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        self.error_label.hide()
        self.retry_button.hide()
        self.exit_button.hide()
        self.activity.show()
        self.current_label.setText("Checking local models…")
        self._worker_result = None
        for label in self.status_labels.values():
            label.setText("Waiting")
            label.setStyleSheet("")

        thread = QThread(self)
        worker = ModelDownloadWorker(self.requirements)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.model_status.connect(self._set_model_status)
        worker.overall_progress.connect(self._set_progress)
        worker.finished.connect(self._worker_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _set_model_status(self, key: str, status: str) -> None:
        label = self.status_labels[key]
        label.setText(status)
        color = theme.SUCCESS if status == "Ready" else theme.ACCENT
        label.setStyleSheet(f"color: {color};")

    def _set_progress(self, completed: int, total: int, current: str) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(completed)
        if completed < total:
            self.current_label.setText(f"Preparing {current} ({completed + 1} of {total})")

    def _worker_finished(self, success: bool, message: str) -> None:
        self._worker_result = (success, message)

    def _thread_finished(self) -> None:
        self.activity.hide()
        self._thread = None
        self._worker = None
        success, message = self._worker_result or (False, "Model setup stopped unexpectedly")
        if success:
            self.progress.setValue(len(self.requirements))
            self.current_label.setText("All models are ready. Starting BellenneRelay…")
            QTimer.singleShot(250, self.ready.emit)
            return
        self.current_label.setText("Model download could not be completed")
        self.error_label.setText(message)
        self.error_label.show()
        self.retry_button.show()
        self.exit_button.show()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt API)
        if self._thread is not None and self._thread.isRunning():
            self.current_label.setText("Please wait for the current model download to finish")
            event.ignore()
            return
        event.accept()
        self._exit_application()

    @staticmethod
    def _exit_application() -> None:
        application = QApplication.instance()
        if application is not None:
            application.quit()
