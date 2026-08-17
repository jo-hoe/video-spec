"""Path confinement: resolve spec-supplied relative paths within their allowed roots.

This is the single choke point for filesystem access. Every path that originates from a
spec passes through here, so ``..`` traversal, absolute paths, and symlink escapes are
rejected in exactly one place.
"""

from __future__ import annotations

from pathlib import Path

from videospec.errors import PathSecurityError


class PathResolver:
    """Confines relative paths to fixed input/output roots."""

    def __init__(self, input_root: Path, output_root: Path) -> None:
        self._input_root = input_root.resolve(strict=True)
        self._output_root = output_root.resolve(strict=True)

    @property
    def input_root(self) -> Path:
        return self._input_root

    @property
    def output_root(self) -> Path:
        return self._output_root

    def resolve_input(self, relative: str) -> Path:
        """Resolve an input path; it must exist within the input root."""
        return self._confine(self._input_root, relative, must_exist=True)

    def resolve_output(self, relative: str) -> Path:
        """Resolve an output path (need not exist yet) within the output root."""
        return self._confine(self._output_root, relative, must_exist=False)

    def confine_to_output(self, candidate: Path) -> Path:
        """Confine an already-constructed path to the output root.

        Used by discovery when building per-file output paths from a base directory.
        """
        resolved = candidate.resolve()
        self._require_within(self._output_root, resolved, str(candidate))
        return resolved

    def _confine(self, root: Path, relative: str, *, must_exist: bool) -> Path:
        candidate = (root / relative).resolve()
        self._require_within(root, candidate, relative)
        if must_exist and not candidate.exists():
            raise PathSecurityError(relative)
        return candidate

    @staticmethod
    def _require_within(root: Path, candidate: Path, label: str) -> None:
        if not candidate.is_relative_to(root):
            raise PathSecurityError(label)
