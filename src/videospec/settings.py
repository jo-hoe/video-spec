"""Runtime settings sourced from environment variables (with ``VIDEOSPEC_`` prefix).

These describe *where* things live (spec path, mounted roots, tool locations) and how
verbose logging is. Processing parameters (concurrency, operation arguments) live in the
spec itself, not here.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven runtime configuration."""

    model_config = SettingsConfigDict(env_prefix="VIDEOSPEC_", frozen=True)

    spec_path: Path = Field(default=Path("/work/spec/spec.yaml"))
    input_root: Path = Field(default=Path("/work/input"))
    output_root: Path = Field(default=Path("/work/output"))
    # Scratch space for intermediate artifacts (sprite sheets, VTT). Lives inside the
    # container by default and is not volume-mounted unless the operator opts in.
    work_root: Path = Field(default=Path("/work/tmp"))
    ffmpeg: str = "ffmpeg"
    ffprobe: str = "ffprobe"
    log_level: str = "INFO"
