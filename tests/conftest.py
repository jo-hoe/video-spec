"""Shared test fixtures and a fake command runner."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from videospec.ffmpeg.runner import CompletedCommand
from videospec.ffmpeg.tools import ToolPaths
from videospec.security.paths import PathResolver

# A response is a function taking the argv and returning a CompletedCommand.
Responder = Callable[[tuple[str, ...]], CompletedCommand]


class FakeRunner:
    """A :class:`CommandRunner` that records argv and returns scripted responses.

    ``on`` maps a substring found in argv[0] (the program) to a responder; a default
    responder handles anything unmatched. Recorded calls are available via ``calls``.
    """

    def __init__(self, default: Responder | None = None) -> None:
        self.calls: list[tuple[str, ...]] = []
        self._responders: list[tuple[str, Responder]] = []
        self._default = default or self._ok

    def on(self, program_substring: str, responder: Responder) -> FakeRunner:
        self._responders.append((program_substring, responder))
        return self

    def run(self, argv: Sequence[str]) -> CompletedCommand:
        argv_tuple = tuple(argv)
        self.calls.append(argv_tuple)
        program = argv_tuple[0] if argv_tuple else ""
        for needle, responder in self._responders:
            if needle in program:
                return responder(argv_tuple)
        return self._default(argv_tuple)

    @staticmethod
    def _ok(argv: tuple[str, ...]) -> CompletedCommand:
        return CompletedCommand(argv=argv, returncode=0, stdout="", stderr="")


def probe_duration_response(seconds: float) -> Responder:
    """Responder emitting ffprobe JSON for a given duration."""
    payload = json.dumps({"format": {"duration": str(seconds)}})
    return lambda argv: CompletedCommand(argv=argv, returncode=0, stdout=payload, stderr="")


@pytest.fixture
def tools() -> ToolPaths:
    return ToolPaths(ffmpeg="ffmpeg", ffprobe="ffprobe")


@pytest.fixture
def roots(tmp_path: Path) -> tuple[Path, Path]:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    return input_root, output_root


@pytest.fixture
def resolver(roots: tuple[Path, Path]) -> PathResolver:
    input_root, output_root = roots
    return PathResolver(input_root, output_root)
