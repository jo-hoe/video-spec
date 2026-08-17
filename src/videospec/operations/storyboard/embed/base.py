"""Container-specific embedding strategies (strategy pattern)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from videospec.ffmpeg.tools import ToolPaths


@runtime_checkable
class ContainerEmbedder(Protocol):
    """Builds the ffmpeg argv that muxes the storyboard into a specific container."""

    def build_argv(
        self,
        tools: ToolPaths,
        input_path: Path,
        vtt_path: Path,
        sprites: list[Path],
        output_path: Path,
    ) -> list[str]:
        """Return the ffmpeg argv embedding ``vtt_path`` + ``sprites`` into the output."""
        ...
