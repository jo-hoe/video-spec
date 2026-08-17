"""argv builders for frame extraction and container embedding."""

from __future__ import annotations

from pathlib import Path

from videospec.ffmpeg.tools import ToolPaths
from videospec.models.storyboard import StoryboardOperation
from videospec.operations.storyboard.embed.mkv import MkvEmbedder
from videospec.operations.storyboard.embed.mp4 import Mp4Embedder
from videospec.operations.storyboard.frames import (
    build_tile_argv,
    discover_sheets,
    sheet_output_pattern,
)


def test_tile_argv_filter_and_output(tools: ToolPaths) -> None:
    op = StoryboardOperation(
        interval_seconds=10, columns=5, rows=5, tile_width=160, tile_height=90, jpeg_quality=4
    )
    argv = build_tile_argv(tools, op, Path("/in/a.mp4"), Path("/work"))
    assert "fps=1/10,scale=160:90,tile=5x5" in argv
    assert argv[argv.index("-qscale:v") + 1] == "4"
    assert argv[-1] == str(sheet_output_pattern(Path("/work"), "storyboard"))
    assert "-i" in argv and argv[argv.index("-i") + 1] == str(Path("/in/a.mp4"))


def test_discover_sheets_returns_pages_in_order(tmp_path: Path) -> None:
    # Create out of order to prove sorting.
    for page in (2, 1, 3):
        (tmp_path / f"storyboard-{page:03d}.jpg").write_bytes(b"jpeg")
    (tmp_path / "storyboard.vtt").write_bytes(b"x")  # non-sheet file must be ignored
    sheets = discover_sheets(tmp_path, "storyboard")
    assert [p.name for p in sheets] == [
        "storyboard-001.jpg",
        "storyboard-002.jpg",
        "storyboard-003.jpg",
    ]


def test_discover_sheets_empty_when_none(tmp_path: Path) -> None:
    assert discover_sheets(tmp_path, "storyboard") == []


def test_mkv_embed_argv(tools: ToolPaths) -> None:
    argv = MkvEmbedder().build_argv(
        tools,
        Path("/in/a.mp4"),
        Path("/work/storyboard.vtt"),
        [Path("/work/storyboard-001.jpg"), Path("/work/storyboard-002.jpg")],
        Path("/out/a.mkv"),
    )
    assert argv[:2] == [tools.ffmpeg, "-hide_banner"]
    assert argv.count("-attach") == 2
    assert "-c:s" in argv and argv[argv.index("-c:s") + 1] == "webvtt"
    assert "-c" in argv and argv[argv.index("-c") + 1] == "copy"
    assert "filename=storyboard-001.jpg" in argv
    assert "filename=storyboard-002.jpg" in argv
    # per-attachment indexed metadata
    assert "-metadata:s:t:0" in argv
    assert "-metadata:s:t:1" in argv
    assert argv[-1] == str(Path("/out/a.mkv"))


def test_mp4_embed_argv_uses_mov_text_and_cover(tools: ToolPaths) -> None:
    argv = Mp4Embedder().build_argv(
        tools,
        Path("/in/a.mp4"),
        Path("/work/storyboard.vtt"),
        [Path("/work/storyboard-001.jpg")],
        Path("/out/a.mp4"),
    )
    assert argv[argv.index("-c:s") + 1] == "mov_text"
    assert "attached_pic" in argv
    assert argv.count("-i") == 3  # input, vtt, cover
    assert argv[-1] == str(Path("/out/a.mp4"))


def test_mp4_embed_argv_without_sprites(tools: ToolPaths) -> None:
    argv = Mp4Embedder().build_argv(
        tools, Path("/in/a.mp4"), Path("/work/storyboard.vtt"), [], Path("/out/a.mp4")
    )
    assert "attached_pic" not in argv
    assert argv.count("-i") == 2  # input + vtt only
