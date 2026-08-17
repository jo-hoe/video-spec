"""Resolved locations of the external tools videospec drives."""

from __future__ import annotations

from dataclasses import dataclass

from videospec.settings import Settings


@dataclass(frozen=True)
class ToolPaths:
    """Executable names/paths for ffmpeg and ffprobe."""

    ffmpeg: str
    ffprobe: str

    @classmethod
    def from_settings(cls, settings: Settings) -> ToolPaths:
        return cls(ffmpeg=settings.ffmpeg, ffprobe=settings.ffprobe)
