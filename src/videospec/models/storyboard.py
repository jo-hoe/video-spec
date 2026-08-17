"""The storyboard operation model and its output-container enum."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from videospec.models.base import StrictModel

# A positive integer, reused across tile/grid dimensions.
PositiveInt = Annotated[int, Field(gt=0)]


class Container(StrEnum):
    """Output container for an operation.

    MKV is the reliable target for embedding a sprite attachment plus a native WebVTT
    subtitle stream. MP4 is supported too, with a documented portability caveat handled
    by the MP4 embed strategy.
    """

    MKV = "mkv"
    MP4 = "mp4"

    @property
    def extension(self) -> str:
        """File extension (without dot) for this container."""
        return self.value


class StoryboardOperation(StrictModel):
    """Generate storyboard sprite sheet(s) + WebVTT and embed them into the output video.

    Every field except ``type`` has a sensible default, so a minimal operation is simply
    ``{"type": "storyboard"}``.
    """

    type: Literal["storyboard"] = "storyboard"
    interval_seconds: PositiveInt = 10
    columns: PositiveInt = 5
    rows: PositiveInt = 5
    tile_width: PositiveInt = 160
    tile_height: PositiveInt = 90
    # ffmpeg JPEG qscale: 2 (best) .. 31 (worst).
    jpeg_quality: Annotated[int, Field(ge=2, le=31)] = 4
    sprite_basename: Annotated[str, Field(pattern=r"^[A-Za-z0-9._-]+$")] = "storyboard"
    # strict=False so the enum accepts its string value ("mkv"/"mp4") from YAML while the
    # rest of the model stays strict. This is still a single type: a Container value.
    container: Annotated[Container, Field(strict=False)] = Container.MKV

    @property
    def tiles_per_sheet(self) -> int:
        """Number of tiles packed into a single sprite sheet."""
        return self.columns * self.rows
