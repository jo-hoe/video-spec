# syntax=docker/dockerfile:1

FROM python:3.14-slim AS base

# ffmpeg (and ffprobe) provide the media tooling this service orchestrates.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching. Fall back to a plain resolve when
# no lockfile is present in the build context.
COPY pyproject.toml README.md LICENSE ./
COPY uv.loc[k] ./
RUN if [ -f uv.lock ]; then uv sync --frozen --no-install-project --no-dev; \
    else uv sync --no-install-project --no-dev; fi

COPY src ./src
RUN uv sync --no-dev

# Runtime directories mounted as volumes; created up front so a non-root user can write.
RUN mkdir -p /work/spec /work/input /work/output /work/tmp

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /work /app
USER appuser

ENTRYPOINT ["uv", "run", "--no-dev", "python", "-m", "videospec"]
