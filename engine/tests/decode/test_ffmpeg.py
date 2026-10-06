import subprocess
from contextlib import closing
from pathlib import Path

import numpy as np
import pytest

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import iter_luma, iter_rgb, probe, to_cells
from nostrobe.errors import DecodeError, UnsupportedMediaError
from nostrobe.luminance.curve import code10_to_cd_m2
from nostrobe.synth.generator import ClipSpec, iter_frames, smoke_specs, write_clip


@pytest.mark.parametrize("code", [16, 64, 128, 200, 235])
def test_flat_round_trip(tmp_path: Path, code: int) -> None:
    spec = ClipSpec(f"flat_{code}", "flat", width=320, height=180, duration_s=0.2, code8=code)
    path = write_clip(tmp_path, spec)
    info = probe(path)
    assert info.fps == 25 and (info.width, info.height) == (320, 180)
    decoded = list(iter_luma(path, grid=(320, 180)))
    assert len(decoded) == 5
    np.testing.assert_allclose([pts for _, pts in decoded], np.arange(5) / 25)
    for frame, _ in decoded:
        assert np.max(np.abs(frame.astype(int) - code)) <= 1
        expected = float(code10_to_cd_m2(np.array(code * 4)))
        error_one_code = max(
            abs(float(code10_to_cd_m2(np.array(code * 4 + delta))) - expected) for delta in (-4, 4)
        )
        assert np.max(np.abs(to_cells(frame) - expected)) <= error_one_code + 1e-9
    tags = json_probe(path)["streams"][0]
    assert all(tags[key] == "bt709" for key in ("color_transfer", "color_space", "color_primaries"))
    assert tags["color_range"] == "tv" and tags["pix_fmt"] == "yuv420p"


def json_probe(path: Path) -> dict:
    import json

    return json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)]
        )
    )


def test_cell_averaging_is_linear() -> None:
    frame = np.tile(np.array([[16, 235], [235, 16]], dtype=np.uint8), (90, 160))
    np.testing.assert_allclose(to_cells(frame), 100)
    average_code = code10_to_cd_m2(np.array([frame.mean() * 4]))[0]
    assert abs(average_code - 100) > 20


def test_spatial_checker_gate(tmp_path: Path) -> None:
    spec = ClipSpec("checker", "checker", duration_s=0.2, dark_cd_m2=0, delta_cd_m2=200)
    path = write_clip(tmp_path, spec)
    original = next(iter_frames(spec))
    reference = to_cells(original)
    with closing(iter_luma(path)) as decoded:
        frame, _ = next(decoded)
    assert np.max(np.abs(to_cells(frame) - reference)) < 1


def test_rgb_decode(tmp_path: Path) -> None:
    spec = ClipSpec("red", "red", duration_s=0.2, width=320, height=180)
    path = write_clip(tmp_path, spec)
    with closing(iter_rgb(path)) as decoded:
        frame, pts = next(decoded)
    assert frame.shape[-1] == 3 and frame.dtype == np.uint8 and pts == 0
    assert frame[..., 0].mean() > 250 and frame[..., 1:].mean() < 4


def test_early_close_reaps_decoder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_clip(tmp_path, ClipSpec("early", "flat", duration_s=2))
    real_popen = subprocess.Popen
    processes = []

    def capture(*args, **kwargs):
        result = real_popen(*args, **kwargs)
        processes.append(result)
        return result

    monkeypatch.setattr("nostrobe.decode.ffmpeg.subprocess.Popen", capture)
    decoded = iter_luma(path)
    next(decoded)
    decoded.close()
    assert processes and all(process.poll() is not None for process in processes)
    assert all(process.stdout.closed and process.stderr.closed for process in processes)


def test_probe_and_decode_errors(tmp_path: Path) -> None:
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not video")
    with pytest.raises(DecodeError):
        probe(bad)
    path = write_clip(tmp_path, ClipSpec("flat", "flat", duration_s=0.2))
    with pytest.raises(DecodeError, match="could not start decoder"):
        next(iter_luma(path, settings=Settings(ffmpeg="/nonexistent/ffmpeg")))


@pytest.mark.parametrize("transfer", ["smpte2084", "arib-std-b67", "unknown"])
def test_rejects_hdr_and_unknown_transfer(tmp_path: Path, transfer: str) -> None:
    source = write_clip(tmp_path, ClipSpec("flat", "flat", duration_s=0.2))
    target = tmp_path / "tagged.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:v",
            "libx264",
            "-x264-params",
            "colorprim=bt709:colormatrix=bt709:transfer="
            + ("undef" if transfer == "unknown" else transfer),
            str(target),
        ],
        check=True,
    )
    with pytest.raises(UnsupportedMediaError):
        probe(target)


def test_variable_frame_rate_timestamps(tmp_path: Path) -> None:
    source = write_clip(tmp_path, ClipSpec("vfr", "flat", duration_s=1, width=320, height=180))
    target = tmp_path / "vfr.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-vf",
            "select='not(mod(n,3))'",
            "-fps_mode",
            "vfr",
            "-c:v",
            "libx264",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
            "-color_primaries",
            "bt709",
            "-color_range",
            "tv",
            str(target),
        ],
        check=True,
    )
    times = [pts for _, pts in iter_luma(target)]
    np.testing.assert_allclose(times, np.arange(0, 25, 3) / 25, atol=1e-6)


def test_invalid_cell_grid() -> None:
    with pytest.raises(ValueError):
        to_cells(np.zeros((179, 320), dtype=np.uint8))


@pytest.mark.parametrize(
    "spec", [spec for spec in smoke_specs() if not spec.is_rgb], ids=lambda spec: spec.name
)
def test_full_synthetic_suite_linear_error(tmp_path: Path, spec: ClipSpec) -> None:
    path = write_clip(tmp_path, spec)
    for (decoded, _), raw in zip(iter_luma(path), iter_frames(spec), strict=True):
        assert np.max(np.abs(to_cells(decoded) - to_cells(raw))) < 1


@pytest.mark.parametrize("fps", [24, 30, 60])
def test_integer_pts_preserve_one_second_boundaries(tmp_path: Path, fps: int) -> None:
    """Six-digit showinfo pts_time can move a frame across the one-second window."""
    spec = ClipSpec("exact_pts", "flat", duration_s=2, fps=fps, width=320, height=180)
    times = np.array([t for _, t in iter_luma(write_clip(tmp_path, spec), grid=(320, 180))])
    np.testing.assert_allclose(times, np.arange(2 * fps) / fps, atol=1e-12, rtol=0)
