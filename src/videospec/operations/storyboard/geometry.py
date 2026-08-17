"""Pure geometry for storyboard layout: map thumbnail indices to sprite-sheet tiles.

No I/O and no ffmpeg here, so this is trivially unit-testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from videospec.models.storyboard import StoryboardOperation


@dataclass(frozen=True)
class Thumbnail:
    """One thumbnail's placement and the time window it represents."""

    index: int
    start: float  # seconds, inclusive
    end: float  # seconds, exclusive (clamped to duration for the last thumbnail)
    sheet: int  # 0-based sprite-sheet page
    x: int
    y: int
    width: int
    height: int

    @property
    def sheet_number(self) -> int:
        """1-based page number, matching the ``%03d`` ffmpeg output numbering."""
        return self.sheet + 1


@dataclass(frozen=True)
class StoryboardLayout:
    """The full set of thumbnails plus the sheet count."""

    thumbnails: tuple[Thumbnail, ...]
    sheet_count: int


def thumbnail_count(duration: float, interval_seconds: int) -> int:
    """Number of thumbnails sampled at ``interval_seconds`` across ``duration``."""
    if duration <= 0:
        return 0
    return math.ceil(duration / interval_seconds)


def plan_layout(duration: float, op: StoryboardOperation) -> StoryboardLayout:
    """Compute every thumbnail's time window and tile position.

    The sheet count here is *predicted* from duration and interval. ffmpeg is the source
    of truth for how many sheets are actually produced, so call :func:`clamp_to_sheets`
    with the real count before rendering the VTT (see the storyboard handler).
    """
    count = thumbnail_count(duration, op.interval_seconds)
    thumbnails = tuple(_thumbnail_at(i, duration, op) for i in range(count))
    sheet_count = math.ceil(count / op.tiles_per_sheet) if count else 0
    return StoryboardLayout(thumbnails=thumbnails, sheet_count=sheet_count)


def clamp_to_sheets(layout: StoryboardLayout, actual_sheet_count: int) -> StoryboardLayout:
    """Drop thumbnails whose sheet page ffmpeg did not actually produce.

    Guards against the predicted page count exceeding what ended up on disk (VFR/clipped
    sources), which would otherwise leave WebVTT cues pointing at a missing sprite sheet.
    """
    if actual_sheet_count >= layout.sheet_count:
        return layout
    kept = tuple(t for t in layout.thumbnails if t.sheet < actual_sheet_count)
    return StoryboardLayout(thumbnails=kept, sheet_count=actual_sheet_count)


def _thumbnail_at(index: int, duration: float, op: StoryboardOperation) -> Thumbnail:
    start = index * op.interval_seconds
    end = min(start + op.interval_seconds, duration)
    sheet, slot = divmod(index, op.tiles_per_sheet)
    row, col = divmod(slot, op.columns)
    return Thumbnail(
        index=index,
        start=float(start),
        end=float(end),
        sheet=sheet,
        x=col * op.tile_width,
        y=row * op.tile_height,
        width=op.tile_width,
        height=op.tile_height,
    )
