"""Logging configuration."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configure root logging once, with a concise, structured-ish format."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
