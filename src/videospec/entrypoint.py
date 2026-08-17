"""Process entrypoint: load settings + spec, run the orchestrator, map the exit code."""

from __future__ import annotations

import logging
import sys

import videospec.operations  # noqa: F401 - populate the registry via import side effects
from videospec.errors import VideoSpecError
from videospec.ffmpeg.runner import SubprocessRunner
from videospec.ffmpeg.tools import ToolPaths
from videospec.logging_config import configure_logging
from videospec.models.spec_loader import load_spec
from videospec.operations.registry import REGISTRY
from videospec.orchestrator.orchestrator import ItemOutcome, Orchestrator
from videospec.security.paths import PathResolver
from videospec.settings import Settings

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_CONFIG = 2


def main() -> int:
    """Run videospec end to end. Returns a process exit code."""
    settings = Settings()
    configure_logging(settings.log_level)
    try:
        return _run(settings)
    except VideoSpecError as exc:
        logger.error("%s", exc)
        return EXIT_CONFIG


def _run(settings: Settings) -> int:
    spec = load_spec(settings.spec_path)
    # A log_level in the spec overrides the environment default.
    if spec.log_level is not None:
        configure_logging(spec.log_level.value)
    resolver = PathResolver(settings.input_root, settings.output_root)
    settings.work_root.mkdir(parents=True, exist_ok=True)
    orchestrator = Orchestrator(
        resolver=resolver,
        runner=SubprocessRunner(),
        tools=ToolPaths.from_settings(settings),
        registry=REGISTRY,
        work_root=settings.work_root,
    )
    outcomes = orchestrator.run(spec)
    return _exit_code(outcomes)


def _exit_code(outcomes: list[ItemOutcome]) -> int:
    failures = [o for o in outcomes if not o.ok]
    if failures:
        logger.error("%d of %d item(s) failed", len(failures), len(outcomes))
        return EXIT_FAILURE
    logger.info("completed %d item(s) successfully", len(outcomes))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
