"""Model strictness and defaults."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from videospec.models.spec import Spec
from videospec.models.storyboard import Container, StoryboardOperation


def _spec_data(
    op_over: dict[str, Any] | None = None,
    job_over: dict[str, Any] | None = None,
    spec_over: dict[str, Any] | None = None,
) -> dict[str, Any]:
    operation: dict[str, Any] = {"type": "storyboard", **(op_over or {})}
    job: dict[str, Any] = {
        "input": "a.mp4",
        "output": "out",
        "operations": [operation],
        **(job_over or {}),
    }
    return {"job": job, **(spec_over or {})}


def test_minimal_operation_applies_all_defaults() -> None:
    spec = Spec.model_validate(_spec_data())
    op = spec.job.operations[0]
    assert isinstance(op, StoryboardOperation)
    assert (op.interval_seconds, op.columns, op.rows) == (10, 5, 5)
    assert (op.tile_width, op.tile_height, op.jpeg_quality) == (160, 90, 4)
    assert op.container is Container.MKV
    assert spec.concurrency == 1
    assert spec.job.recursive is False


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(op_over={"nope": 1}))


def test_string_int_is_rejected_in_strict_mode() -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(op_over={"interval_seconds": "10"}))


@pytest.mark.parametrize("value", [0, -5])
def test_interval_must_be_positive(value: int) -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(op_over={"interval_seconds": value}))


@pytest.mark.parametrize("value", [1, 32])
def test_jpeg_quality_bounds(value: int) -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(op_over={"jpeg_quality": value}))


def test_concurrency_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(spec_over={"concurrency": 0}))


def test_empty_operations_rejected() -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(job_over={"operations": []}))


def test_unknown_operation_type_rejected() -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(job_over={"operations": [{"type": "reencode"}]}))


def test_container_extension() -> None:
    assert Container.MKV.extension == "mkv"
    assert Container.MP4.extension == "mp4"


@pytest.mark.parametrize(("value", "expected"), [("mkv", Container.MKV), ("mp4", Container.MP4)])
def test_container_accepts_string_value(value: str, expected: Container) -> None:
    spec = Spec.model_validate(_spec_data(op_over={"container": value}))
    assert spec.job.operations[0].container is expected


def test_container_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        Spec.model_validate(_spec_data(op_over={"container": "avi"}))


def test_tiles_per_sheet() -> None:
    op = StoryboardOperation(columns=8, rows=4)
    assert op.tiles_per_sheet == 32
