"""Embed strategy selection keyed on the output container."""

from __future__ import annotations

from videospec.errors import OperationError
from videospec.models.storyboard import Container
from videospec.operations.storyboard.embed.base import ContainerEmbedder
from videospec.operations.storyboard.embed.mkv import MkvEmbedder
from videospec.operations.storyboard.embed.mp4 import Mp4Embedder

_EMBEDDERS: dict[Container, ContainerEmbedder] = {
    Container.MKV: MkvEmbedder(),
    Container.MP4: Mp4Embedder(),
}


def get_embed_strategy(container: Container) -> ContainerEmbedder:
    """Return the embedder for ``container`` or raise :class:`OperationError`."""
    try:
        return _EMBEDDERS[container]
    except KeyError as exc:  # pragma: no cover - guarded by the Container enum
        raise OperationError(f"no embed strategy for container {container!r}") from exc


__all__ = ["ContainerEmbedder", "get_embed_strategy"]
