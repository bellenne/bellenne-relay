"""Minimal Windows global hotkeys using RegisterHotKey."""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

LOGGER = logging.getLogger(__name__)


class GlobalHotkeys(QObject):
    toggle_translation = Signal()
    toggle_subtitles = Signal()
    toggle_overlay_editing = Signal()
    registration_error = Signal(str)

    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_NOREPEAT = 0x4000
    WM_HOTKEY = 0x0312
    WM_QUIT = 0x0012

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()

    def start(self) -> None:
        if sys.platform != "win32" or self._thread is not None:
            return
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._message_loop, name="global-hotkeys", daemon=False
        )
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def stop(self) -> None:
        if self._thread is None:
            return
        if self._thread_id is not None:
            ctypes.windll.user32.PostThreadMessageW(
                self._thread_id, self.WM_QUIT, 0, 0
            )
        self._thread.join(timeout=3.0)
        if self._thread.is_alive():
            LOGGER.error("Global hotkey thread did not stop")
        self._thread = None
        self._thread_id = None

    def _message_loop(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        mapping = {
            1: (ord("T"), self.toggle_translation),
            2: (ord("S"), self.toggle_subtitles),
            3: (ord("O"), self.toggle_overlay_editing),
        }
        registered = []
        modifiers = self.MOD_CONTROL | self.MOD_ALT | self.MOD_NOREPEAT
        for identifier, (virtual_key, _signal) in mapping.items():
            if user32.RegisterHotKey(None, identifier, modifiers, virtual_key):
                registered.append(identifier)
            else:
                self.registration_error.emit(
                    f"Could not register Ctrl+Alt+{chr(virtual_key)} "
                    f"(Windows error {ctypes.get_last_error()})."
                )
        self._ready.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            if message.message == self.WM_HOTKEY and message.wParam in mapping:
                mapping[message.wParam][1].emit()
        for identifier in registered:
            user32.UnregisterHotKey(None, identifier)

