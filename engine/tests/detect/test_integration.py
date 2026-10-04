import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from typer.testing import CliRunner

from nostrobe.cli import app
from nostrobe.decode.ffmpeg import iter_analysis, iter_luma, iter_rgb
from nostrobe.detect.pipeline import analyze_detect, analyze_detect_all
from nostrobe.synth.generator import TruthInterval, analytic_truth, encode, smoke_specs

FPS = (24, 25, 30, 50, 60)


def interval_iou(events, truth):
    points = sorted(
        {t for e in events for t in (e.t_start, e.t_end)}
        | {t for e in truth for t in (e.t_start, e.t_end)}
    )
    intersection = union = 0.0
    for a, b in zip(points, points[1:], strict=False):
        found = any(e.t_start <= a and b <= e.t_end for e in events)
        expected = any(e.t_start <= a and b <= e.t_end for e in truth)
        union += (b - a) * (found or expected)
        intersection += (b - a) * (found and expected)
    return intersection / union if union else 1.0


def independent_dense_intervals(spec, limit):
    """Profile timing oracle for dense square waves; no detector invocation.

    S1 truth remains authoritative for Broadcast. Kids uses its own >4 policy,
    which cannot be compared with Broadcast's later >6 onset.
    """
    indices = np.arange(spec.n_frames)
    time = indices / spec.fps
    states = time * spec.rate % 1 >= 1 - spec.duty
    if spec.primitive == "camera_burst":
        states &= (time >= 0.5) & (time < 2.5)
    edges = indices[1:][states[1:] != states[:-1]]
    hot = [np.count_nonzero((edges > i - spec.fps) & (edges <= i)) > limit for i in indices]
    result = []
    start = None
    for i, active in enumerate([*hot, False]):
        if active and start is None:
            start = i / spec.fps
        elif not active and start is not None:
            result.append(TruthInterval(t_start=start, t_end=min(i / spec.fps, spec.duration_s)))
            start = None
    return result


@pytest.mark.parametrize("fps", FPS)
@pytest.mark.parametrize("spec", smoke_specs(), ids=lambda spec: spec.name)
def test_encoded_s1_smoke_truth_all_frame_rates(tmp_path, spec, fps):
    spec = replace(spec, fps=fps)
    path = tmp_path / f"HAZARD_{spec.name}.mp4"
    encode(path, spec)
    truth = analytic_truth(spec)
    events = analyze_detect_all(path)
    broadcast_fails = [e for e in events["broadcast"] if e.severity == "fail"]
    assert bool(broadcast_fails) == (truth.label == "must_fail")
    if truth.label == "must_fail":
        assert interval_iou(broadcast_fails, truth.expected_intervals) >= 0.9
        for profile in ("local", "kids"):
            detected = [e for e in events[profile] if e.severity == "fail"]
            assert detected
            expected_timing = (
                truth.expected_intervals
                if profile == "local"
                else (independent_dense_intervals(spec, 4))
            )
            assert interval_iou(detected, expected_timing) >= 0.9
    for profile in ("local", "kids"):
        expected = truth.label == "must_fail" or spec.name == "area_24"
        if profile == "kids":
            expected |= spec.name in ("rate_3", "isolated_3")
        assert any(e.severity == "fail" for e in events[profile]) == expected


def test_combined_decode_matches_independent_paths_and_cli(tmp_path):
    path = tmp_path / "HAZARD_combined.mp4"
    encode(path, smoke_specs()[2])
    combined = list(iter_analysis(path))
    luma, rgb = list(iter_luma(path)), list(iter_rgb(path))
    assert len(combined) == len(luma) == len(rgb)
    for (y, color, time), (reference_y, yt), (reference_rgb, rt) in zip(
        combined, luma, rgb, strict=True
    ):
        assert time == yt == rt
        np.testing.assert_array_equal(y, reference_y)
        np.testing.assert_array_equal(color, reference_rgb)
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", str(path), "--detect-only"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["verified"] is False
    assert set(report["profiles"]) == {"broadcast", "local", "kids"}
    output = tmp_path / "events.json"
    result = runner.invoke(
        app,
        ["analyze", str(path), "--detect-only", "--profile", "broadcast", "--output", str(output)],
    )
    assert result.exit_code == 0
    assert set(json.loads(output.read_text())["profiles"]) == {"broadcast"}
    result = runner.invoke(app, ["analyze", str(path), "--detect-only", "--profile", "typo"])
    assert result.exit_code == 5
    result = runner.invoke(
        app, ["analyze", str(path), "--detect-only", "--output", str(tmp_path / "unsafe.hzt.json")]
    )
    assert result.exit_code == 1
    assert not (tmp_path / "unsafe.hzt.json").exists()
    original = path.read_bytes()
    result = runner.invoke(app, ["analyze", str(path), "--detect-only", "--output", str(path)])
    assert result.exit_code == 1
    assert path.read_bytes() == original


@given(fps=st.sampled_from(FPS), name=st.sampled_from(["rate_3_5", "area_26", "delta_21"]))
@settings(max_examples=5, deadline=None, derandomize=True)
def test_resolution_invariance_encoded(fps, name):
    with TemporaryDirectory() as folder:
        selected = next(s for s in smoke_specs() if s.name == name)
        results = []
        for width, height in ((1280, 720), (1920, 1080)):
            spec = replace(selected, fps=fps, width=width, height=height)
            path = Path(folder) / f"HAZARD_res_{width}.mp4"
            encode(path, spec)
            results.append(analyze_detect_all(path))
        for profile in ("broadcast", "local", "kids"):
            left, right = results[0][profile], results[1][profile]
            assert len(left) == len(right)
            for a, b in zip(left, right, strict=True):
                assert (a.kind, a.severity) == (b.kind, b.severity)
                assert abs(a.t_start - b.t_start) <= 1 / fps + 1e-9
                assert abs(a.t_end - b.t_end) <= 1 / fps + 1e-9


def test_public_single_profile_api(tmp_path):
    path = tmp_path / "HAZARD_api.mp4"
    encode(path, smoke_specs()[2])
    assert analyze_detect(path) == analyze_detect_all(path)["broadcast"]


def test_analysis_refuses_non_bt709_color_tags(tmp_path):
    import subprocess

    from nostrobe.decode.ffmpeg import probe
    from nostrobe.errors import UnsupportedMediaError

    source = tmp_path / "HAZARD_bt709.mp4"
    target = tmp_path / "rec601.mp4"
    encode(source, smoke_specs()[0])
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:v",
            "copy",
            "-bsf:v",
            "h264_metadata=colour_primaries=6:transfer_characteristics=6:matrix_coefficients=6",
            str(target),
        ],
        check=True,
    )
    # The existing luma-only reader stays usable; RGB analysis must not apply
    # the BT.709 matrix/transfer to explicitly different source colorimetry.
    assert probe(target).transfer == "sdr"
    with pytest.raises(UnsupportedMediaError, match="BT.709"):
        analyze_detect_all(target)
