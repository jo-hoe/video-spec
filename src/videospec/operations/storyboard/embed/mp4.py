"""MP4 embedding: WebVTT as a mov_text subtitle track + first sprite as cover art.

MP4 has no generic attachment stream like MKV, so only the first sprite sheet can ride
along (as an attached picture / cover art) and the WebVTT is converted to ``mov_text``.
Most web players expect *sidecar* sprite+VTT files for MP4 storyboards, so embedded MP4
storyboards may not be read by every player. The handler logs this caveat.
"""

from __future__ import annotations

from pathlib import Path

from videospec.ffmpeg.tools import ToolPaths


class Mp4Embedder:
    """Embed the storyboard into an MP4 container (best-effort)."""

    def build_argv(
        self,
        tools: ToolPaths,
        input_path: Path,
        vtt_path: Path,
        sprites: list[Path],
        output_path: Path,
    ) -> list[str]:
        argv = [
            tools.ffmpeg,
            "-hide_banner",
            "-y",
            "-i",
            str(input_path),
            "-i",
            str(vtt_path),
        ]
        cover = sprites[0] if sprites else None
        if cover is not None:
            argv += ["-i", str(cover)]
        argv += ["-map", "0", "-map", "1"]
        if cover is not None:
            argv += ["-map", "2"]
        argv += ["-c", "copy", "-c:s", "mov_text"]
        if cover is not None:
            # Mark the extra image stream as attached cover art.
            argv += ["-c:v:1", "mjpeg", "-disposition:v:1", "attached_pic"]
        argv += ["-metadata:s:s:0", "title=Storyboard", str(output_path)]
        return argv
