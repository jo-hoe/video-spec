"""Command execution abstraction.

All external tool calls go through the :class:`CommandRunner` protocol so tests can
inject a fake. The concrete :class:`SubprocessRunner` never uses a shell and always
passes an ``argv`` list, eliminating shell-injection risk.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from videospec.errors import FFmpegError


@dataclass(frozen=True)
class CompletedCommand:
    """The outcome of running a command."""

    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@runtime_checkable
class CommandRunner(Protocol):
    """Runs an ``argv`` and returns its result, raising on failure."""

    def run(self, argv: Sequence[str]) -> CompletedCommand:
        """Execute ``argv``; raise :class:`FFmpegError` on a non-zero exit."""
        ...


class SubprocessRunner:
    """Runs commands via :func:`subprocess.run` with ``shell=False`` (never a string)."""

    def run(self, argv: Sequence[str]) -> CompletedCommand:
        argv_tuple = tuple(argv)
        # shell=False with an argv list: no interpolation, no injection surface.
        proc = subprocess.run(
            list(argv_tuple),
            capture_output=True,
            text=True,
            check=False,
        )
        result = CompletedCommand(
            argv=argv_tuple,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
        if proc.returncode != 0:
            raise FFmpegError(result)
        return result
