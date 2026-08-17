"""Orchestrate one spec: discover work items and process them concurrently."""

from __future__ import annotations

import logging
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from videospec.discovery.discovery import VideoDiscovery, WorkItem
from videospec.ffmpeg.ffprobe import FFprobe
from videospec.ffmpeg.runner import CommandRunner
from videospec.ffmpeg.tools import ToolPaths
from videospec.models.spec import Spec, VideoJob
from videospec.models.storyboard import Container
from videospec.operations.base import OperationContext
from videospec.operations.registry import OperationRegistry
from videospec.security.paths import PathResolver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ItemOutcome:
    """Result of processing a single work item."""

    item: WorkItem
    ok: bool
    error: str | None = None


class Orchestrator:
    """Runs a spec's single job across all discovered videos concurrently."""

    def __init__(
        self,
        resolver: PathResolver,
        runner: CommandRunner,
        tools: ToolPaths,
        registry: OperationRegistry,
        work_root: Path,
    ) -> None:
        self._resolver = resolver
        self._runner = runner
        self._tools = tools
        self._registry = registry
        self._work_root = work_root
        self._discovery = VideoDiscovery(resolver, FFprobe(runner, tools))

    def run(self, spec: Spec) -> list[ItemOutcome]:
        """Process the spec; return an outcome per work item. Never raises per item."""
        container = _job_container(spec.job)
        items = self._discovery.expand(spec.job, container)
        if not items:
            logger.warning("no videos matched job input %r", spec.job.input)
            return []
        logger.info("processing %d video(s) with concurrency=%d", len(items), spec.concurrency)
        indexed = list(enumerate(items))
        with ThreadPoolExecutor(max_workers=spec.concurrency) as pool:
            return list(pool.map(lambda pair: self._process(spec.job, pair[0], pair[1]), indexed))

    def _process(self, job: VideoJob, index: int, item: WorkItem) -> ItemOutcome:
        work_dir = self._work_root / f"item-{index:04d}"
        try:
            self._process_item(job, item, work_dir)
        except Exception as exc:  # isolate one item's failure from its siblings
            logger.error("failed processing %s: %s", item.input_path, exc)
            return ItemOutcome(item=item, ok=False, error=str(exc))
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        return ItemOutcome(item=item, ok=True)

    def _process_item(self, job: VideoJob, item: WorkItem, work_dir: Path) -> None:
        item.output_path.parent.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)
        for op in job.operations:
            handler = self._registry.handler_for(op)
            ctx = OperationContext(
                input_path=item.input_path,
                output_path=item.output_path,
                work_dir=work_dir,
                runner=self._runner,
                tools=self._tools,
                resolver=self._resolver,
            )
            handler.run(op, ctx)


def _job_container(job: VideoJob) -> Container:
    """The output container for the job, taken from its (single) operation."""
    return job.operations[0].container
