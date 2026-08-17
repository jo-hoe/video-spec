"""MKV embedding: WebVTT subtitle stream + sprite sheet(s) as file attachments."""

from __future__ import annotations

from pathlib import Path

from videospec.ffmpeg.tools import ToolPaths


class MkvEmbedder:
    """Embed the storyboard into a Matroska (.mkv) container.

    The WebVTT rides as a native ``webvtt`` subtitle stream; each sprite sheet is added as
    a file attachment whose ``filename`` matches what the VTT ``#xywh`` cues reference, so
    players resolve the tiles by attachment name. Audio/video are stream-copied.
    """

    def build_argv(
        self,
        tools: ToolPaths,
        input_path: Path,
        vtt_path: Path,
        sprites: list[Path],
        output_path: Path,
    ) -> list[str]:
        argv = [tools.ffmpeg, "-hide_banner", "-y", "-i", str(input_path), "-i", str(vtt_path)]
        for position, sprite in enumerate(sprites):
            argv += self._attachment_args(position, sprite)
        argv += [
            "-map",
            "0",
            "-map",
            "1",
            "-c",
            "copy",
            "-c:s",
            "webvtt",
            "-metadata:s:s:0",
            "title=Storyboard",
            str(output_path),
        ]
        return argv

    @staticmethod
    def _attachment_args(position: int, sprite: Path) -> list[str]:
        return [
            "-attach",
            str(sprite),
            f"-metadata:s:t:{position}",
            "mimetype=image/jpeg",
            f"-metadata:s:t:{position}",
            f"filename={sprite.name}",
        ]
