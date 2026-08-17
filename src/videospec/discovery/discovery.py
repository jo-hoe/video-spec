"""Expand one job's source (file or directory) into concrete work items.

Discovery is the only place the filesystem decides file-vs-directory, keeping the spec
models free of polymorphic fields. Non-video files in a directory are probed and skipped.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from videospec.ffmpeg.ffprobe import FFprobe
from videospec.models.spec import VideoJob
from videospec.models.storyboard import Container
from videospec.security.paths import PathResolver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkItem:
    """One resolved (input, output) pair to process."""

    input_path: Path
    output_path: Path


class VideoDiscovery:
    """Expands a :class:`VideoJob` into confined, probed :class:`WorkItem` s."""

    def __init__(self, resolver: PathResolver, probe: FFprobe) -> None:
        self._resolver = resolver
        self._probe = probe

    def expand(self, job: VideoJob, container: Container) -> list[WorkItem]:
        source = self._resolver.resolve_input(job.input)
        if source.is_dir():
            return list(self._expand_directory(job, source, container))
        return [self._file_item(job, source, container)]

    def _file_item(self, job: VideoJob, source: Path, container: Container) -> WorkItem:
        output = self._resolver.resolve_output(job.output)
        return WorkItem(input_path=source, output_path=self._with_ext(output, container))

    def _expand_directory(
        self, job: VideoJob, source: Path, container: Container
    ) -> Iterator[WorkItem]:
        output_base = self._resolver.resolve_output(job.output)
        for candidate in self._iter_files(source, job.recursive):
            if not self._probe.has_video_stream(candidate):
                logger.warning("skipping non-video file: %s", candidate)
                continue
            yield self._directory_item(source, output_base, candidate, container)

    def _directory_item(
        self, source: Path, output_base: Path, candidate: Path, container: Container
    ) -> WorkItem:
        relative = candidate.relative_to(source)
        target = output_base / relative
        confined = self._resolver.confine_to_output(self._with_ext(target, container))
        return WorkItem(input_path=candidate, output_path=confined)

    @staticmethod
    def _iter_files(source: Path, recursive: bool) -> Iterator[Path]:
        entries = source.rglob("*") if recursive else source.iterdir()
        return (entry for entry in sorted(entries) if entry.is_file())

    @staticmethod
    def _with_ext(path: Path, container: Container) -> Path:
        return path.with_suffix(f".{container.extension}")
