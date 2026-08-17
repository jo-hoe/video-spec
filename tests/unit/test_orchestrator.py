"""Orchestrator: work-item fan-out, failure isolation, output dirs."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from tests.conftest import FakeRunner
from videospec.ffmpeg.runner import CompletedCommand
from videospec.ffmpeg.tools import ToolPaths
from videospec.models.spec import Spec
from videospec.operations.base import OperationContext, OperationResult
from videospec.operations.registry import OperationRegistry
from videospec.orchestrator.orchestrator import Orchestrator
from videospec.security.paths import PathResolver


def _spec(input_: str, output: str, recursive: bool = False) -> Spec:
    return Spec.model_validate(
        {
            "concurrency": 4,
            "job": {
                "input": input_,
                "output": output,
                "recursive": recursive,
                "operations": [{"type": "storyboard"}],
            },
        }
    )


def _registry_recording(seen: list[Path], fail_on: str | None = None) -> OperationRegistry:
    registry = OperationRegistry()
    from videospec.models.storyboard import StoryboardOperation

    @registry.register(StoryboardOperation)
    class _Handler:
        def run(self, op: BaseModel, ctx: OperationContext) -> OperationResult:
            seen.append(ctx.input_path)
            if fail_on and ctx.input_path.name == fail_on:
                raise RuntimeError("boom")
            ctx.output_path.write_bytes(b"out")
            return OperationResult(output_path=ctx.output_path, artifacts=())

    return registry


def _video_probe_runner() -> FakeRunner:
    return FakeRunner().on(
        "ffprobe",
        lambda argv: CompletedCommand(
            argv=argv, returncode=0, stdout='{"streams":[{"codec_type":"video"}]}', stderr=""
        ),
    )


def _orchestrator(
    resolver: PathResolver, tools: ToolPaths, registry: OperationRegistry, work_root: Path
) -> Orchestrator:
    return Orchestrator(resolver, _video_probe_runner(), tools, registry, work_root)


def test_all_items_succeed(
    resolver: PathResolver, roots: tuple[Path, Path], tools: ToolPaths, tmp_path: Path
) -> None:
    input_root, output_root = roots
    src = input_root / "in"
    src.mkdir()
    (src / "a.mp4").write_bytes(b"x")
    (src / "b.mp4").write_bytes(b"x")
    seen: list[Path] = []

    outcomes = _orchestrator(resolver, tools, _registry_recording(seen), tmp_path / "work").run(
        _spec("in", "out")
    )

    assert len(outcomes) == 2
    assert all(o.ok for o in outcomes)
    assert (output_root / "out" / "a.mkv").exists()
    assert {p.name for p in seen} == {"a.mp4", "b.mp4"}


def test_one_failure_does_not_abort_siblings(
    resolver: PathResolver, roots: tuple[Path, Path], tools: ToolPaths, tmp_path: Path
) -> None:
    input_root, output_root = roots
    src = input_root / "in"
    src.mkdir()
    (src / "good.mp4").write_bytes(b"x")
    (src / "bad.mp4").write_bytes(b"x")

    registry = _registry_recording([], fail_on="bad.mp4")
    outcomes = _orchestrator(resolver, tools, registry, tmp_path / "work").run(_spec("in", "out"))

    by_name = {o.item.input_path.name: o for o in outcomes}
    assert by_name["good.mp4"].ok is True
    assert by_name["bad.mp4"].ok is False
    assert by_name["bad.mp4"].error == "boom"
    assert (output_root / "out" / "good.mkv").exists()


def test_no_matches_returns_empty(
    resolver: PathResolver, roots: tuple[Path, Path], tools: ToolPaths, tmp_path: Path
) -> None:
    (roots[0] / "empty").mkdir()
    outcomes = _orchestrator(resolver, tools, _registry_recording([]), tmp_path / "work").run(
        _spec("empty", "out")
    )
    assert outcomes == []
