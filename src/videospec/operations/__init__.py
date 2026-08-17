"""Operation package.

Importing this package imports every handler module for its registration side effect, so
``videospec.operations.registry.REGISTRY`` is fully populated after import.
"""

from __future__ import annotations

# Register handlers by importing them. Add future handlers here.
from videospec.operations.storyboard import handler as _storyboard_handler  # noqa: F401

__all__: list[str] = []
