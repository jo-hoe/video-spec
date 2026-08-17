"""The storyboard handler: probe -> tile -> render VTT -> embed."""

from __future__ import annotations

import logging
from pathlib import Path

from videospec.ffmpeg.ffprobe import FFprobe
from videospec.models.storyboard import Container, StoryboardOperation
from videospec.operations.base import OperationContext, OperationResult
from videospec.operations.registry import REGISTRY
from videospec.operations.storyboard import frames, vtt
from videospec.operations.storyboard.embed import get_embed_strategy
from videospec.operations.storyboard.geometry import StoryboardLayout, plan_layout

logger = logging.getLogger(__name__)


@REGISTRY.register(StoryboardOperation)
class StoryboardHandler:
    """Generates storyboard sprite sheet(s) + WebVTT and embeds them into the output."""

    def run(self, op: StoryboardOperation, ctx: OperationContext) -> OperationResult:
        duration = FFprobe(ctx.runner, ctx.tools).duration_seconds(ctx.input_path)
        layout = plan_layout(duration, op)
        self._extract_sheets(op, ctx)
        vtt_path = self._write_vtt(op, ctx, layout)
        sprites = self._collect_sheets(op, ctx, layout)
        self._embed(op, ctx, vtt_path, sprites)
        return OperationResult(output_path=ctx.output_path, artifacts=(vtt_path, *sprites))

    def _extract_sheets(self, op: StoryboardOperation, ctx: OperationContext) -> None:
        argv = frames.build_tile_argv(ctx.tools, op, ctx.input_path, ctx.work_dir)
        ctx.runner.run(argv)

    def _write_vtt(
        self, op: StoryboardOperation, ctx: OperationContext, layout: StoryboardLayout
    ) -> Path:
        vtt_path = ctx.work_dir / f"{op.sprite_basename}.vtt"
        vtt_path.write_text(vtt.render_vtt(layout, op.sprite_basename), encoding="utf-8")
        return vtt_path

    def _collect_sheets(
        self, op: StoryboardOperation, ctx: OperationContext, layout: StoryboardLayout
    ) -> list[Path]:
        sprites = [
            ctx.work_dir / vtt.sprite_filename(op.sprite_basename, page)
            for page in range(1, layout.sheet_count + 1)
        ]
        return [sprite for sprite in sprites if sprite.exists()]

    def _embed(
        self,
        op: StoryboardOperation,
        ctx: OperationContext,
        vtt_path: Path,
        sprites: list[Path],
    ) -> None:
        if op.container is Container.MP4:
            logger.warning(
                "MP4 storyboard embedding is best-effort; most players expect sidecar "
                "sprite+VTT files. Prefer MKV for reliable embedded storyboards."
            )
        embedder = get_embed_strategy(op.container)
        argv = embedder.build_argv(ctx.tools, ctx.input_path, vtt_path, sprites, ctx.output_path)
        ctx.runner.run(argv)
