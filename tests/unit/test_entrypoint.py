"""Entrypoint exit-code mapping."""

from __future__ import annotations

from pathlib import Path

from videospec.discovery.discovery import WorkItem
from videospec.entrypoint import EXIT_FAILURE, EXIT_OK, _exit_code
from videospec.orchestrator.orchestrator import ItemOutcome


def _outcome(ok: bool) -> ItemOutcome:
    item = WorkItem(input_path=Path("in.mp4"), output_path=Path("out.mkv"))
    return ItemOutcome(item=item, ok=ok, error=None if ok else "x")


def test_exit_ok_when_all_succeed() -> None:
    assert _exit_code([_outcome(True), _outcome(True)]) == EXIT_OK


def test_exit_ok_when_empty() -> None:
    assert _exit_code([]) == EXIT_OK


def test_exit_failure_when_any_fail() -> None:
    assert _exit_code([_outcome(True), _outcome(False)]) == EXIT_FAILURE
