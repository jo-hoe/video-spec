"""StoryboardHandler orchestration with a fake runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import FakeRunner, probe_duration_response
from videospec.ffmpeg.runner import CompletedCommand
from videospec.ffmpeg.tools import ToolPaths
from videospec.models.storyboard import Container, StoryboardOperation
from videospec.operations.base import OperationContext
from videospec.operations.storyboard.handler import StoryboardHandler


def _context(
    tmp_path: Path, runner: FakeRunner, tools: ToolPaths, container: Container
) -> OperationContext:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return OperationContext(
        input_path=tmp_path / "in.mp4",
        output_path=tmp_path / f"out.{container.extension}",
        work_dir=work_dir,
        runner=runner,
        tools=tools,
        resolver=None,  # type: ignore[arg-type]  # handler does not use the resolver
    )


def _runner_that_creates_sheets(work_dir: Path, basename: str, pages: int) -> FakeRunner:
    def make_sheets(argv: tuple[str, ...]) -> CompletedCommand:
        # Only the tiling call writes sheets (its output pattern ends in -%03d.jpg).
        if any(arg.endswith("-%03d.jpg") for arg in argv):
            for page in range(1, pages + 1):
                (work_dir / f"{basename}-{page:03d}.jpg").write_bytes(b"jpeg")
        return CompletedCommand(argv=argv, returncode=0, stdout="", stderr="")

    runner = FakeRunner(default=make_sheets)
    runner.on("ffprobe", probe_duration_response(25.0))
    return runner


def test_handler_runs_probe_tile_embed_in_order(tmp_path: Path, tools: ToolPaths) -> None:
    op = StoryboardOperation(interval_seconds=10, columns=5, rows=5, container=Container.MKV)
    ctx = _context(tmp_path, FakeRunner(), tools, Container.MKV)
    runner = _runner_that_creates_sheets(ctx.work_dir, op.sprite_basename, pages=1)
    ctx = OperationContext(
        input_path=ctx.input_path,
        output_path=ctx.output_path,
        work_dir=ctx.work_dir,
        runner=runner,
        tools=tools,
        resolver=ctx.resolver,
    )

    result = StoryboardHandler().run(op, ctx)

    programs = [call[0] for call in runner.calls]
    assert programs == ["ffprobe", "ffmpeg", "ffmpeg"]  # probe, tile, embed
    vtt_path = ctx.work_dir / f"{op.sprite_basename}.vtt"
    assert vtt_path.exists()
    assert result.output_path == ctx.output_path
    assert vtt_path in result.artifacts


def test_handler_mp4_logs_caveat(
    tmp_path: Path, tools: ToolPaths, caplog: pytest.LogCaptureFixture
) -> None:
    op = StoryboardOperation(container=Container.MP4)
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    runner = _runner_that_creates_sheets(work_dir, op.sprite_basename, pages=1)
    ctx = OperationContext(
        input_path=tmp_path / "in.mp4",
        output_path=tmp_path / "out.mp4",
        work_dir=work_dir,
        runner=runner,
        tools=tools,
        resolver=None,  # type: ignore[arg-type]
    )
    with caplog.at_level("WARNING"):
        StoryboardHandler().run(op, ctx)
    assert any("MP4 storyboard embedding is best-effort" in r.message for r in caplog.records)
