"""Base Pydantic model enforcing strict, non-fuzzy typing across every spec model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Immutable, strictly-typed base model.

    - ``extra="forbid"``: unknown YAML keys are rejected (catches typos).
    - ``frozen=True``: parsed specs are immutable.
    - ``strict=True``: no implicit coercion (e.g. ``"10"`` is not accepted for an int
      field), so a parameter never silently accepts more than one type.
    - ``validate_default=True``: defaults are validated too.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
    )
