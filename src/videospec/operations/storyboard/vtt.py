"""Pure WebVTT rendering for storyboard cues.

Given a layout and the sprite filename pattern, produces the WebVTT text mapping each
time window to a sprite tile via the ``#xywh`` media-fragment syntax.
"""

from __future__ import annotations

from videospec.operations.storyboard.geometry import StoryboardLayout, Thumbnail


def sprite_filename(basename: str, sheet_number: int) -> str:
    """The sprite sheet filename for a 1-based page, matching ffmpeg's ``%03d`` output."""
    return f"{basename}-{sheet_number:03d}.jpg"


def render_vtt(layout: StoryboardLayout, sprite_basename: str) -> str:
    """Render the full WebVTT document for ``layout``."""
    cues = [_render_cue(thumb, sprite_basename) for thumb in layout.thumbnails]
    return "\n".join(["WEBVTT", "", *cues])


def _render_cue(thumb: Thumbnail, sprite_basename: str) -> str:
    sprite = sprite_filename(sprite_basename, thumb.sheet_number)
    fragment = f"{sprite}#xywh={thumb.x},{thumb.y},{thumb.width},{thumb.height}"
    return f"{_format_timestamp(thumb.start)} --> {_format_timestamp(thumb.end)}\n{fragment}\n"


def _format_timestamp(seconds: float) -> str:
    """Format seconds as WebVTT ``HH:MM:SS.mmm``."""
    millis_total = round(seconds * 1000)
    hours, remainder = divmod(millis_total, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
