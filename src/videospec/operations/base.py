"""The operation handler contract shared by every operation implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from videospec.ffmpeg.runner import CommandRunner
from videospec.ffmpeg.tools import ToolPaths
from videospec.security.paths import PathResolver

# Contravariant: a handler for a broad model type also handles narrower ones.
OpT_contra = TypeVar("OpT_contra", bound=BaseModel, contravariant=True)


@dataclass(frozen=True)
class OperationContext:
    """Everything a handler needs to process one input into one output."""

    input_path: Path
    output_path: Path
    work_dir: Path
    runner: CommandRunner
    tools: ToolPaths
    resolver: PathResolver


@dataclass(frozen=True)
class OperationResult:
    """What an operation produced."""

    output_path: Path
    artifacts: tuple[Path, ...]


@runtime_checkable
class OperationHandler(Protocol[OpT_contra]):
    """Executes a single, already-validated operation model of type ``OpT_contra``."""

    def run(self, op: OpT_contra, ctx: OperationContext) -> OperationResult:
        """Run the operation described by ``op`` within ``ctx``."""
        ...
