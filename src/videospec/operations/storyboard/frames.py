"""Pure builder for the frame-extraction + tiling ffmpeg argv (single pass)."""

from __future__ import annotations

from pathlib import Path

from videospec.ffmpeg.tools import ToolPaths
from videospec.models.storyboard import StoryboardOperation


def sheet_output_pattern(work_dir: Path, sprite_basename: str) -> Path:
    """The ``%03d`` output pattern ffmpeg writes numbered sprite sheets to."""
    return work_dir / f"{sprite_basename}-%03d.jpg"


def discover_sheets(work_dir: Path, sprite_basename: str) -> list[Path]:
    """Return the sprite sheets ffmpeg actually wrote, in page order.

    We cannot rely on a predicted sheet count: ``fps=1/N`` may emit a different number of
    frames than ``ceil(duration / N)`` for variable-frame-rate or oddly-clipped sources,
    so the real page count is whatever ended up on disk. Globbing the actual files is the
    source of truth for both the attachments and the WebVTT cues.
    """
    return sorted(work_dir.glob(f"{sprite_basename}-*.jpg"))


def build_tile_argv(
    tools: ToolPaths,
    op: StoryboardOperation,
    input_path: Path,
    work_dir: Path,
) -> list[str]:
    """Build the ffmpeg argv that samples frames and tiles them into sprite sheet(s).

    One pass: ``fps=1/N`` samples a frame every N seconds, ``scale`` resizes to the tile
    size, ``tile=CxR`` packs them into a grid, numbered ``basename-%03d.jpg``.
    """
    vfilter = (
        f"fps=1/{op.interval_seconds},"
        f"scale={op.tile_width}:{op.tile_height},"
        f"tile={op.columns}x{op.rows}"
    )
    return [
        tools.ffmpeg,
        "-hide_banner",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vfilter,
        "-qscale:v",
        str(op.jpeg_quality),
        str(sheet_output_pattern(work_dir, op.sprite_basename)),
    ]
