"""Path confinement security."""

from __future__ import annotations

from pathlib import Path

import pytest

from videospec.errors import PathSecurityError
from videospec.security.paths import PathResolver


def test_roots_exposed(resolver: PathResolver, roots: tuple[Path, Path]) -> None:
    input_root, output_root = roots
    assert resolver.input_root == input_root.resolve()
    assert resolver.output_root == output_root.resolve()


def test_resolves_valid_input(resolver: PathResolver, roots: tuple[Path, Path]) -> None:
    input_root, _ = roots
    (input_root / "a.mp4").write_text("x", encoding="utf-8")
    assert resolver.resolve_input("a.mp4") == (input_root / "a.mp4").resolve()


def test_missing_input_raises(resolver: PathResolver) -> None:
    with pytest.raises(PathSecurityError):
        resolver.resolve_input("missing.mp4")


@pytest.mark.parametrize("evil", ["../secret", "../../etc/passwd", "sub/../../escape"])
def test_traversal_rejected(resolver: PathResolver, evil: str) -> None:
    with pytest.raises(PathSecurityError):
        resolver.resolve_output(evil)


def test_absolute_path_rejected(resolver: PathResolver) -> None:
    with pytest.raises(PathSecurityError):
        resolver.resolve_output("C:/Windows/System32/x")


def test_output_need_not_exist(resolver: PathResolver, roots: tuple[Path, Path]) -> None:
    _, output_root = roots
    assert resolver.resolve_output("new/out.mkv") == (output_root / "new/out.mkv").resolve()


def test_confine_to_output_rejects_escape(resolver: PathResolver, roots: tuple[Path, Path]) -> None:
    _, output_root = roots
    with pytest.raises(PathSecurityError):
        resolver.confine_to_output(output_root.parent / "escape.mkv")


def test_confine_to_output_accepts_inside(resolver: PathResolver, roots: tuple[Path, Path]) -> None:
    _, output_root = roots
    inside = output_root / "sub" / "x.mkv"
    assert resolver.confine_to_output(inside) == inside.resolve()
