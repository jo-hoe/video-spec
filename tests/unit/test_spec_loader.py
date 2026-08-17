"""Spec loader error handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from videospec.errors import SpecError
from videospec.models.spec_loader import load_spec


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_valid_spec(tmp_path: Path) -> None:
    spec_file = _write(
        tmp_path / "spec.yaml",
        "version: 1\nconcurrency: 3\njob:\n  input: a\n  output: b\n"
        "  operations:\n    - type: storyboard\n",
    )
    spec = load_spec(spec_file)
    assert spec.concurrency == 3
    assert spec.job.input == "a"


def test_missing_file_raises_spec_error(tmp_path: Path) -> None:
    with pytest.raises(SpecError, match="cannot read"):
        load_spec(tmp_path / "nope.yaml")


def test_invalid_yaml_raises_spec_error(tmp_path: Path) -> None:
    spec_file = _write(tmp_path / "spec.yaml", "job: [unclosed")
    with pytest.raises(SpecError, match="not valid YAML"):
        load_spec(spec_file)


def test_non_mapping_top_level_raises(tmp_path: Path) -> None:
    spec_file = _write(tmp_path / "spec.yaml", "- 1\n- 2\n")
    with pytest.raises(SpecError, match="mapping at the top level"):
        load_spec(spec_file)


def test_schema_violation_raises_spec_error(tmp_path: Path) -> None:
    spec_file = _write(tmp_path / "spec.yaml", "version: 1\njob:\n  input: a\n")
    with pytest.raises(SpecError, match="failed validation"):
        load_spec(spec_file)
