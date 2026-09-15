from __future__ import annotations

from app.text_safety import SOFT_BREAK, collapse_pathological_runs, soft_wrap_unbroken_text
from app.ui.widgets.transcript_view import latest_row_scroll_value


def test_soft_wrap_preserves_visible_text_and_whitespace() -> None:
    text = "Short  Supercalifragilisticexpialidocious\nNext"

    wrapped = soft_wrap_unbroken_text(text, chunk_size=8)

    assert wrapped.replace(SOFT_BREAK, "") == text
    assert "Short  " in wrapped
    assert all(len(piece) <= 8 for piece in wrapped.split()[1].split(SOFT_BREAK))


def test_pathological_character_run_is_collapsed() -> None:
    text = "No" + "o" * 500

    collapsed = collapse_pathological_runs(text)

    assert collapsed == "N" + "o" * 12 + "…"


def test_normal_expressive_text_is_not_changed() -> None:
    assert collapse_pathological_runs("Nooooo way!!!") == "Nooooo way!!!"


def test_latest_short_row_is_revealed_without_scrolling_to_feed_maximum() -> None:
    assert latest_row_scroll_value(
        row_top=900,
        row_height=100,
        viewport_height=500,
        maximum=900,
    ) == 508


def test_tall_latest_row_scrolls_to_its_beginning() -> None:
    assert latest_row_scroll_value(
        row_top=900,
        row_height=700,
        viewport_height=500,
        maximum=1200,
    ) == 892
