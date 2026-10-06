import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from nostrobe.decode.ffmpeg import iter_analysis, probe
from nostrobe.errors import DecodeError
from nostrobe.synth.generator import ClipSpec, write_clip


@pytest.mark.parametrize("fps", ["0/0", "25/0", "0/1", "nan", "-25/1"])
def test_invalid_frame_rate_is_a_typed_decode_error(tmp_path: Path, fps: str) -> None:
    source = tmp_path / "invalid.mp4"
    source.write_bytes(b"fixture")
    stream = {
        "color_transfer": "bt709",
        "color_range": "tv",
        "pix_fmt": "yuv420p",
        "avg_frame_rate": fps,
        "duration": "1",
        "width": 320,
        "height": 180,
    }
    result = subprocess.CompletedProcess([], 0, json.dumps({"streams": [stream]}).encode())
    with patch("nostrobe.decode.ffmpeg.subprocess.run", return_value=result):
        with pytest.raises(DecodeError):
            probe(source)


def test_zero_length_and_corrupt_inputs_are_typed(tmp_path: Path) -> None:
    for name, content in [("empty.mp4", b""), ("corrupt.mp4", b"not an mp4")]:
        source = tmp_path / name
        source.write_bytes(content)
        with pytest.raises(DecodeError):
            next(iter_analysis(source))


def test_4k_silent_input_decodes_to_bounded_analysis_grid(tmp_path: Path) -> None:
    source = write_clip(tmp_path, ClipSpec("4k", "flat", width=3840, height=2160, duration_s=0.08))
    media = probe(source, require_bt709=True)
    assert (media.width, media.height) == (3840, 2160)
    frames = list(iter_analysis(source))
    assert len(frames) == 2
    assert all(y.shape == (360, 640) and rgb.shape == (360, 640, 3) for y, rgb, _ in frames)
