"""WebVTT rendering (golden output)."""

from __future__ import annotations

from videospec.models.storyboard import StoryboardOperation
from videospec.operations.storyboard.geometry import plan_layout
from videospec.operations.storyboard.vtt import render_vtt, sprite_filename


def test_sprite_filename_zero_padded() -> None:
    assert sprite_filename("storyboard", 1) == "storyboard-001.jpg"
    assert sprite_filename("sb", 12) == "sb-012.jpg"


def test_render_vtt_golden() -> None:
    op = StoryboardOperation(interval_seconds=10, columns=2, rows=2, tile_width=160, tile_height=90)
    layout = plan_layout(25, op)
    expected = (
        "WEBVTT\n"
        "\n"
        "00:00:00.000 --> 00:00:10.000\n"
        "storyboard-001.jpg#xywh=0,0,160,90\n"
        "\n"
        "00:00:10.000 --> 00:00:20.000\n"
        "storyboard-001.jpg#xywh=160,0,160,90\n"
        "\n"
        "00:00:20.000 --> 00:00:25.000\n"
        "storyboard-001.jpg#xywh=0,90,160,90\n"
    )
    assert render_vtt(layout, op.sprite_basename) == expected


def test_render_vtt_empty_layout() -> None:
    op = StoryboardOperation()
    layout = plan_layout(0, op)
    assert render_vtt(layout, op.sprite_basename) == "WEBVTT\n"


def test_timestamp_hours_component() -> None:
    op = StoryboardOperation(interval_seconds=3600, columns=1, rows=2)
    layout = plan_layout(7200, op)
    body = render_vtt(layout, op.sprite_basename)
    assert "01:00:00.000 --> 02:00:00.000" in body
