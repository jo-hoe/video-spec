"""Exception hierarchy for videospec.

All domain errors derive from :class:`VideoSpecError` so the entrypoint can map any
expected failure to a non-zero exit code while letting unexpected errors propagate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from videospec.ffmpeg.runner import CompletedCommand


class VideoSpecError(Exception):
    """Base class for all expected, user-facing videospec errors."""


class SpecError(VideoSpecError):
    """The YAML spec is missing, unreadable, or fails schema validation."""


class PathSecurityError(VideoSpecError):
    """A spec-supplied path escaped its allowed root or did not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(f"path is outside its allowed root or does not exist: {path!r}")
        self.path = path


class OperationError(VideoSpecError):
    """An operation could not be dispatched or executed."""


class FFmpegError(VideoSpecError):
    """An ffmpeg/ffprobe invocation exited with a non-zero status."""

    def __init__(self, command: CompletedCommand) -> None:
        program = command.argv[0] if command.argv else "<empty>"
        super().__init__(
            f"{program} exited with code {command.returncode}: {command.stderr.strip()}"
        )
        self.command = command
