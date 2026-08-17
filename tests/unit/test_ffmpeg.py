"""Embed strategy selection and ffprobe parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import FakeRunner, probe_duration_response
from videospec.errors import FFmpegError
from videospec.ffmpeg.ffprobe import FFprobe
from videospec.ffmpeg.runner import CompletedCommand
from videospec.ffmpeg.tools import ToolPaths
from videospec.models.storyboard import Container
from videospec.operations.storyboard.embed import get_embed_strategy
from videospec.operations.storyboard.embed.mkv import MkvEmbedder
from videospec.operations.storyboard.embed.mp4 import Mp4Embedder


def test_get_embed_strategy() -> None:
    assert isinstance(get_embed_strategy(Container.MKV), MkvEmbedder)
    assert isinstance(get_embed_strategy(Container.MP4), Mp4Embedder)


def test_ffprobe_duration(tools: ToolPaths) -> None:
    runner = FakeRunner().on("ffprobe", probe_duration_response(42.5))
    assert FFprobe(runner, tools).duration_seconds(Path("/in/a.mp4")) == 42.5


def test_ffprobe_duration_bad_payload(tools: ToolPaths) -> None:
    runner = FakeRunner().on(
        "ffprobe",
        lambda argv: CompletedCommand(argv=argv, returncode=0, stdout="{}", stderr=""),
    )
    with pytest.raises(FFmpegError):
        FFprobe(runner, tools).duration_seconds(Path("/in/a.mp4"))


def test_ffprobe_has_video_stream_true(tools: ToolPaths) -> None:
    payload = '{"streams": [{"codec_type": "video"}]}'
    runner = FakeRunner().on(
        "ffprobe",
        lambda argv: CompletedCommand(argv=argv, returncode=0, stdout=payload, stderr=""),
    )
    assert FFprobe(runner, tools).has_video_stream(Path("/in/a.mp4")) is True


def test_ffprobe_has_video_stream_false_when_no_streams(tools: ToolPaths) -> None:
    runner = FakeRunner().on(
        "ffprobe",
        lambda argv: CompletedCommand(argv=argv, returncode=0, stdout='{"streams": []}', stderr=""),
    )
    assert FFprobe(runner, tools).has_video_stream(Path("/in/a.txt")) is False


def test_ffprobe_has_video_stream_false_on_error(tools: ToolPaths) -> None:
    def boom(argv: tuple[str, ...]) -> CompletedCommand:
        raise FFmpegError(CompletedCommand(argv=argv, returncode=1, stdout="", stderr="bad"))

    runner = FakeRunner().on("ffprobe", boom)
    assert FFprobe(runner, tools).has_video_stream(Path("/in/a.txt")) is False
