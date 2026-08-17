"""Discovery: single file, directory (recursive/non-recursive), non-video skip, mirroring."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import FakeRunner
from videospec.discovery.discovery import VideoDiscovery
from videospec.ffmpeg.ffprobe import FFprobe
from videospec.ffmpeg.runner import CompletedCommand
from videospec.ffmpeg.tools import ToolPaths
from videospec.models.spec import VideoJob
from videospec.models.storyboard import Container
from videospec.security.paths import PathResolver


def _job(**over: object) -> VideoJob:
    data: dict[str, object] = {
        "input": "in",
        "output": "out",
        "operations": [{"type": "storyboard"}],
    }
    data.update(over)
    return VideoJob.model_validate(data)


def test_single_file(resolver: PathResolver, roots: tuple[Path, Path], tools: ToolPaths) -> None:
    input_root, output_root = roots
    (input_root / "movie.mp4").write_bytes(b"x")
    runner = FakeRunner()
    discovery = VideoDiscovery(resolver, FFprobe(runner, tools))

    items = discovery.expand(_job(input="movie.mp4", output="out.any"), Container.MKV)

    assert len(items) == 1
    assert items[0].input_path == (input_root / "movie.mp4").resolve()
    assert items[0].output_path == (output_root / "out.mkv").resolve()


def test_directory_non_recursive_skips_subdirs_and_non_video(
    resolver: PathResolver, roots: tuple[Path, Path], tools: ToolPaths
) -> None:
    input_root, output_root = roots
    src = input_root / "in"
    (src / "sub").mkdir(parents=True)
    (src / "a.mp4").write_bytes(b"x")
    (src / "notes.txt").write_bytes(b"x")
    (src / "sub" / "deep.mp4").write_bytes(b"x")

    def probe(argv: tuple[str, ...]) -> CompletedCommand:
        streams = '[{"codec_type": "video"}]' if Path(argv[-1]).suffix == ".mp4" else "[]"
        return CompletedCommand(
            argv=argv, returncode=0, stdout=f'{{"streams":{streams}}}', stderr=""
        )

    runner = FakeRunner().on("ffprobe", probe)
    discovery = VideoDiscovery(resolver, FFprobe(runner, tools))

    items = discovery.expand(_job(input="in", output="out", recursive=False), Container.MKV)

    names = {i.input_path.name for i in items}
    assert names == {"a.mp4"}
    assert items[0].output_path == (output_root / "out" / "a.mkv").resolve()


def test_directory_recursive_mirrors_tree(
    resolver: PathResolver, roots: tuple[Path, Path], tools: ToolPaths
) -> None:
    input_root, output_root = roots
    src = input_root / "in"
    (src / "sub").mkdir(parents=True)
    (src / "a.mov").write_bytes(b"x")
    (src / "sub" / "deep.mov").write_bytes(b"x")

    runner = FakeRunner().on(
        "ffprobe",
        lambda argv: CompletedCommand(
            argv=argv, returncode=0, stdout='{"streams":[{"codec_type":"video"}]}', stderr=""
        ),
    )
    discovery = VideoDiscovery(resolver, FFprobe(runner, tools))

    items = discovery.expand(_job(input="in", output="out", recursive=True), Container.MP4)

    outputs = sorted(str(i.output_path) for i in items)
    assert outputs == [
        str((output_root / "out" / "a.mp4").resolve()),
        str((output_root / "out" / "sub" / "deep.mp4").resolve()),
    ]
