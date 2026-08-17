"""End-to-end tests that invoke real ffmpeg/ffprobe.

Deselected by default; run with ``pytest -m integration``. Requires ffmpeg and ffprobe on
PATH (present in the Docker image).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

import videospec.operations  # noqa: F401 - register handlers
from videospec.ffmpeg.runner import SubprocessRunner
from videospec.ffmpeg.tools import ToolPaths
from videospec.models.spec import Spec
from videospec.operations.registry import REGISTRY
from videospec.orchestrator.orchestrator import Orchestrator
from videospec.security.paths import PathResolver

pytestmark = pytest.mark.integration

_HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
skip_no_ffmpeg = pytest.mark.skipif(not _HAVE_FFMPEG, reason="ffmpeg/ffprobe not on PATH")


def _make_clip(path: Path, seconds: int = 12) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=duration={seconds}:size=320x240:rate=5",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def _stream_types(path: Path) -> list[str]:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout.split()


def _has_sprite_attachment(path: Path) -> bool:
    """True if the container carries the sprite as an image attachment/cover art.

    ffprobe reports MKV image attachments as a video stream with ``attached_pic`` and a
    ``filename`` tag, so we check for the sprite filename tag rather than a codec_type.
    """
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream_tags=filename",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return "storyboard-001.jpg" in out.stdout


def _run(tmp_path: Path, container: str) -> Path:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    work_root = tmp_path / "work"
    input_root.mkdir()
    output_root.mkdir()
    work_root.mkdir()
    _make_clip(input_root / "clip.mp4")

    spec = Spec.model_validate(
        {
            "job": {
                "input": "clip.mp4",
                "output": "clip",
                "operations": [
                    {"type": "storyboard", "interval_seconds": 5, "container": container}
                ],
            }
        }
    )
    orchestrator = Orchestrator(
        PathResolver(input_root, output_root),
        SubprocessRunner(),
        ToolPaths(ffmpeg="ffmpeg", ffprobe="ffprobe"),
        REGISTRY,
        work_root,
    )
    outcomes = orchestrator.run(spec)
    assert outcomes and all(o.ok for o in outcomes)
    return output_root / f"clip.{container}"


@skip_no_ffmpeg
def test_storyboard_mkv_has_subtitle_and_attachment(tmp_path: Path) -> None:
    output = _run(tmp_path, "mkv")
    assert output.exists()
    assert "subtitle" in _stream_types(output)
    assert _has_sprite_attachment(output)


@skip_no_ffmpeg
def test_storyboard_mp4_has_subtitle(tmp_path: Path) -> None:
    output = _run(tmp_path, "mp4")
    assert output.exists()
    assert "subtitle" in _stream_types(output)
