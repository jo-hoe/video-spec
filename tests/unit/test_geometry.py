"""Geometry: thumbnail counting and tile placement across sheet boundaries."""

from __future__ import annotations

from videospec.models.storyboard import StoryboardOperation
from videospec.operations.storyboard.geometry import clamp_to_sheets, plan_layout, thumbnail_count


def test_thumbnail_count_rounds_up() -> None:
    assert thumbnail_count(25, 10) == 3
    assert thumbnail_count(20, 10) == 2
    assert thumbnail_count(0, 10) == 0
    assert thumbnail_count(-1, 10) == 0


def test_layout_single_sheet() -> None:
    op = StoryboardOperation(interval_seconds=10, columns=2, rows=2, tile_width=100, tile_height=50)
    layout = plan_layout(35, op)  # 4 thumbnails -> exactly one 2x2 sheet
    assert layout.sheet_count == 1
    assert len(layout.thumbnails) == 4

    first = layout.thumbnails[0]
    assert (first.x, first.y, first.width, first.height) == (0, 0, 100, 50)
    assert (first.start, first.end) == (0.0, 10.0)

    # index 3 -> slot 3 -> row 1, col 1
    last = layout.thumbnails[3]
    assert (last.x, last.y) == (100, 50)
    assert last.sheet == 0


def test_last_thumbnail_end_clamped_to_duration() -> None:
    op = StoryboardOperation(interval_seconds=10)
    layout = plan_layout(25, op)  # last window would be 20..30, clamp to 25
    assert layout.thumbnails[-1].end == 25.0


def test_layout_spills_to_second_sheet() -> None:
    op = StoryboardOperation(interval_seconds=1, columns=2, rows=2)  # 4 per sheet
    layout = plan_layout(5, op)  # 5 thumbnails -> 2 sheets
    assert layout.sheet_count == 2
    fifth = layout.thumbnails[4]
    assert fifth.sheet == 1
    assert fifth.sheet_number == 2
    assert (fifth.x, fifth.y) == (0, 0)  # first slot of the second sheet


def test_clamp_to_sheets_drops_thumbnails_on_missing_pages() -> None:
    op = StoryboardOperation(interval_seconds=1, columns=2, rows=2)  # 4 per sheet
    layout = plan_layout(5, op)  # predicted: 5 thumbnails across 2 sheets
    clamped = clamp_to_sheets(layout, actual_sheet_count=1)  # ffmpeg only wrote 1 sheet
    assert clamped.sheet_count == 1
    assert len(clamped.thumbnails) == 4  # the 5th (on sheet 1) is dropped
    assert all(t.sheet == 0 for t in clamped.thumbnails)


def test_clamp_to_sheets_noop_when_actual_matches_or_exceeds() -> None:
    op = StoryboardOperation(interval_seconds=1, columns=2, rows=2)
    layout = plan_layout(5, op)
    assert clamp_to_sheets(layout, actual_sheet_count=2) is layout
    assert clamp_to_sheets(layout, actual_sheet_count=3) is layout
