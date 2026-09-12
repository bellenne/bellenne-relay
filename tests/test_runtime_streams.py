from __future__ import annotations

import sys

from app.runtime_streams import ensure_standard_streams


def test_missing_gui_standard_streams_get_writable_fallbacks(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    ensure_standard_streams()

    assert sys.stdout is not None
    assert sys.stderr is not None
    assert sys.stdout.write("test") == 4
    assert sys.stderr.write("test") == 4
