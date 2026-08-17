# video-spec

[![CI](https://github.com/jo-hoe/video-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/jo-hoe/video-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Dockerized, one-shot **ffmpeg-orchestration service** that edits one or many videos
according to a strongly-typed YAML spec. The first operation generates **storyboard
sprite sheets** (frames sampled at a fixed interval, tiled into a grid) plus a **WebVTT**
storyboard track, and **embeds both into the output video container** for scrubber-preview
support.

The service is a *wrapper* around ffmpeg — there is no interactive CLI. You provide a YAML
spec and input videos via mounted volumes; the container runs once, processes everything,
and exits with a status code.

## How it works

```
docker compose run --rm videospec
```

- Reads a spec from `VIDEOSPEC_SPEC_PATH` (default `/work/spec/spec.yaml`).
- Discovers input videos from the job's `input` (a single file or a directory, optionally
  recursive). Non-video files in a directory are probed and skipped.
- Runs each video through the job's operation pipeline, in parallel up to the spec's
  `concurrency` (default 1).
- Writes outputs under `VIDEOSPEC_OUTPUT_ROOT` (default `/work/output`), mirroring the
  input tree for directory sources.

## Spec

Exactly one `job`. Every operation argument has a sensible default — only `type` is
required.

```yaml
version: 1
concurrency: 4            # videos processed in parallel (default 1)
job:
  input: clips            # a directory, or a single file like clips/demo.mp4
  output: clips           # output directory (outputs mirror the input tree)
  recursive: true         # discover videos in subfolders (default false)
  operations:
    - type: storyboard    # defaults: interval_seconds=10, columns=5, rows=5,
                          # tile_width=160, tile_height=90, jpeg_quality=4, container=mkv
```

### `storyboard` operation

| field              | type            | default | meaning                                    |
| ------------------ | --------------- | ------- | ------------------------------------------ |
| `type`             | `"storyboard"`  | —       | operation discriminator (required)         |
| `interval_seconds` | int > 0         | `10`    | sample one frame every N seconds           |
| `columns`          | int > 0         | `5`     | sprite-sheet grid columns                  |
| `rows`             | int > 0         | `5`     | sprite-sheet grid rows                     |
| `tile_width`       | int > 0         | `160`   | thumbnail width in pixels                  |
| `tile_height`      | int > 0         | `90`    | thumbnail height in pixels                 |
| `jpeg_quality`     | int 2..31       | `4`     | ffmpeg JPEG qscale (lower = better)        |
| `sprite_basename`  | string          | `storyboard` | output sprite/VTT base name           |
| `container`        | `mkv` \| `mp4`  | `mkv`   | output container                           |

**Container note:** MKV reliably embeds the sprite sheet(s) as attachments plus a native
`webvtt` subtitle stream. MP4 is best-effort — the VTT becomes a `mov_text` track and the
first sprite rides as cover art; most web players expect *sidecar* sprite+VTT files for
MP4, so prefer MKV for embedded storyboards.

## Local development

Requires ffmpeg on PATH for integration tests only.

```bash
python -m venv .venv && . .venv/Scripts/activate      # (Windows Git Bash)
pip install -e ".[dev]"
ruff check .
mypy src
pytest                       # unit tests + coverage (integration deselected)
pytest -m integration        # real ffmpeg (needs ffmpeg/ffprobe on PATH)
```

## Docker

```bash
docker compose build
# place a video under ./input and a spec at ./spec/spec.yaml
docker compose run --rm videospec
# outputs appear under ./output
```

## Architecture

- `models/` — strict, immutable Pydantic models; operations are a discriminated union on
  `type`. No parameter accepts more than one type.
- `operations/` — `OperationHandler` protocol + a registry; each operation self-registers.
  Adding an operation is a new model + handler + registry line; the core never changes.
- `ffmpeg/` — a `CommandRunner` protocol (mockable) that only ever runs `argv` lists
  (never a shell), plus an `ffprobe` wrapper.
- `security/paths.py` — the single choke point confining every spec-supplied path to its
  mounted root (rejects `..`, absolute paths, symlink escapes).
- `discovery/` — expands a job's file-or-directory source into confined work items.
- `orchestrator/` — runs work items concurrently; one failure never aborts the others.
