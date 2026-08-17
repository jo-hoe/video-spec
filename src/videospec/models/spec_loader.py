"""Load and validate a YAML spec into a strongly-typed :class:`Spec`."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from videospec.errors import SpecError
from videospec.models.spec import Spec


def load_spec(path: Path) -> Spec:
    """Read ``path`` as YAML and validate it against the :class:`Spec` schema.

    Raises :class:`SpecError` on a missing/unreadable file, invalid YAML, or a schema
    violation, so the entrypoint can map every expected failure to a clean exit code.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecError(f"cannot read spec file {str(path)!r}: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SpecError(f"spec file {str(path)!r} is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecError(f"spec file {str(path)!r} must contain a mapping at the top level")

    try:
        return Spec.model_validate(data)
    except ValidationError as exc:
        raise SpecError(f"spec file {str(path)!r} failed validation:\n{exc}") from exc
