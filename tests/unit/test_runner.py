"""SubprocessRunner behaviour with a trivial real command."""

from __future__ import annotations

import sys

import pytest

from videospec.errors import FFmpegError
from videospec.ffmpeg.runner import SubprocessRunner


def test_successful_command_captures_stdout() -> None:
    result = SubprocessRunner().run([sys.executable, "-c", "print('hi')"])
    assert result.returncode == 0
    assert "hi" in result.stdout


def test_nonzero_exit_raises_ffmpeg_error() -> None:
    with pytest.raises(FFmpegError):
        SubprocessRunner().run([sys.executable, "-c", "import sys; sys.exit(3)"])
