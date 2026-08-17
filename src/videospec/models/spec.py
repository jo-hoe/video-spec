"""Root spec models: a single job describing what to process and how."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from videospec.models.base import StrictModel
from videospec.models.operations import Operation


class LogLevel(StrEnum):
    """Logging verbosity, mirroring the standard logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class VideoJob(StrictModel):
    """One job: a source (file or directory) run through an ordered operation pipeline.

    ``input`` and ``output`` are paths relative to the input/output roots. Whether
    ``input`` names a file or a directory is a runtime filesystem fact resolved by the
    discovery step, not a polymorphic field on this model.
    """

    input: Annotated[str, Field(min_length=1)]
    output: Annotated[str, Field(min_length=1)]
    # Only meaningful when ``input`` resolves to a directory.
    recursive: bool = False
    operations: Annotated[list[Operation], Field(min_length=1)]


class Spec(StrictModel):
    """Top-level spec: exactly one job plus run-wide settings."""

    version: Literal[1] = 1
    # Number of discovered videos processed in parallel. Defaults to 1; user-settable.
    concurrency: Annotated[int, Field(gt=0)] = 1
    # Optional; when set it overrides the VIDEOSPEC_LOG_LEVEL environment default.
    log_level: Annotated[LogLevel, Field(strict=False)] | None = None
    job: VideoJob
