"""Discriminated union of all operation types.

New operations are added by appending their model to :data:`Operation`; the
``discriminator="type"`` field selects the correct model during validation.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from videospec.models.storyboard import StoryboardOperation

# When a second operation is added, extend this to
# ``Union[StoryboardOperation, ReencodeOperation, ...]``.
Operation = Annotated[
    StoryboardOperation,
    Field(discriminator="type"),
]
