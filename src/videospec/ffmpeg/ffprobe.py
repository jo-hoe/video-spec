"""Thin ffprobe wrapper: query video duration and whether a file has a video stream."""

from __future__ import annotations

import json
from pathlib import Path

from videospec.errors import FFmpegError
from videospec.ffmpeg.runner import CommandRunner
from videospec.ffmpeg.tools import ToolPaths


class FFprobe:
    """Runs ffprobe via a :class:`CommandRunner` and parses its JSON output."""

    def __init__(self, runner: CommandRunner, tools: ToolPaths) -> None:
        self._runner = runner
        self._tools = tools

    def duration_seconds(self, path: Path) -> float:
        """Return the media duration in seconds."""
        argv = [
            self._tools.ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ]
        payload = self._run_json(argv)
        fmt = payload.get("format")
        duration = fmt.get("duration") if isinstance(fmt, dict) else None
        try:
            return float(duration)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise FFmpegError(self._runner.run(argv)) from exc

    def has_video_stream(self, path: Path) -> bool:
        """Return whether ``path`` contains at least one video stream.

        Used by discovery to skip non-video files. A probe failure means "not a video".
        """
        argv = [
            self._tools.ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "json",
            str(path),
        ]
        try:
            payload = self._run_json(argv)
        except FFmpegError:
            return False
        streams = payload.get("streams")
        if not isinstance(streams, list):
            return False
        return any(
            isinstance(stream, dict) and stream.get("codec_type") == "video" for stream in streams
        )

    def _run_json(self, argv: list[str]) -> dict[str, object]:
        completed = self._runner.run(argv)
        try:
            parsed = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise FFmpegError(completed) from exc
        if not isinstance(parsed, dict):
            raise FFmpegError(completed)
        return parsed
