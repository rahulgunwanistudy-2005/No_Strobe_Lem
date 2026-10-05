"""Synthetic unit inputs test the measurer; they are never device evidence."""

import numpy as np
import pytest

from nostrobe.calibration.measure import (
    Capture,
    FrameSignals,
    combine_sync,
    compositing_measurement,
    frame_counter,
    measure_frame,
    sync_measurement,
)
from nostrobe.calibration.stimuli import (
    FPS,
    SYNC_TIMES,
    composite_frames,
    counter,
    sync_frames,
)


def descriptor(kind: str) -> dict[str, object]:
    return {
        "kind": kind,
        "production": False,
        "fps": FPS,
        "duration_s": 24 if kind == "sync" else 30,
        "source_sha256": "0" * 64,
        "patch_times_s": SYNC_TIMES,
        "display_codes": list(range(16, 236)),
        "decoded_luma_codes": (16 + np.arange(16, 236) * 219 / 255).tolist(),
        "cues": [
            {"id": f"case_{i}", "t_on": 3 * (i + 1), "t_off": 3 * (i + 2), "alpha": a, "gray": g}
            for i, (a, g) in enumerate((a, g) for a in (0.25, 0.5, 0.75) for g in (0, 0.25, 0.5))
        ],
    }


def test_binary_frame_counter_survives_every_calibration_veil() -> None:
    frame = np.full((360, 640, 3), 48, dtype=np.uint8)
    for index in [0, 1, 59, 127, 719, 899]:
        counter(frame, index)
        for alpha in [0, 0.25, 0.5, 0.75]:
            for gray in [0, 0.25, 0.5]:
                blended = np.rint((1 - alpha) * frame + alpha * gray * 255).astype(np.uint8)
                assert frame_counter(blended) == index
    with pytest.raises(ValueError, match="references"):
        frame_counter(np.zeros_like(frame))


def test_source_pulse_is_exactly_one_frame_and_small_area() -> None:
    indices = [i for i, frame in enumerate(sync_frames()) if frame[40, 40, 0] == 235]
    assert indices == [t * FPS for t in SYNC_TIMES]
    assert 64 * 32 / (640 * 360) < 0.01
    frame = next(composite_frames())
    assert frame[100, 100, 0] == 16
    assert frame[100, 539, 0] == 235
    assert np.all(frame[80:220, 92:102] == 16)
    assert np.all(frame[80:220, 538:548] == 235)
    assert measure_frame(frame).ramp.tolist() == list(range(16, 236))


def test_signed_sync_offsets_and_required_scenarios() -> None:
    times = np.arange(0, 24, 1 / 60)
    frames = []
    for t in times:
        index = int(round(t * 60)) // 2
        pulse = index in {v * FPS for v in SYNC_TIMES}
        # Synthetic veil is one capture frame late. This is a unit oracle only.
        veil = any(v + 1 / 60 <= t < v + 0.5 + 1 / 60 for v in SYNC_TIMES)
        frames.append(
            FrameSignals(
                index,
                200 if pulse else 48,
                88 if veil else 48,
                np.arange(16, 236, dtype=np.float64),
            )
        )
    capture = Capture(times.tolist(), frames, "test-only", 60)
    run = sync_measurement(capture, descriptor("sync"), "steady")
    assert run["median_s"] == pytest.approx(1 / 60)
    assert len(run["samples"]) == len(SYNC_TIMES)
    with pytest.raises(ValueError, match="three"):
        combine_sync([run])
    combined = combine_sync([run, {**run, "scenario": "seek"}, {**run, "scenario": "pause_resume"}])
    assert combined["sync_tolerance_s"] == 0.1
    frames[120] = FrameSignals(1, 200, 48, frames[120].ramp)
    with pytest.raises(ValueError, match="counter"):
        sync_measurement(capture, descriptor("sync"), "steady")


def test_sync_refuses_missing_edges_and_outlier_bound() -> None:
    frames = [FrameSignals(0, 48, 48, np.zeros(220)) for _ in range(120)]
    with pytest.raises(ValueError, match="five"):
        sync_measurement(
            Capture((np.arange(120) / 60).tolist(), frames, "test", 60),
            descriptor("sync"),
            "steady",
        )
    samples = [{"offset_s": 0}] * 99 + [{"offset_s": 0.5}]
    runs = [
        {"status": "measured", "scenario": s, "samples": samples}
        for s in ["steady", "seek", "pause_resume"]
    ]
    with pytest.raises(ValueError, match="max exceeds"):
        combine_sync(runs)


def test_combined_bound_does_not_dilute_a_slower_playback_scenario() -> None:
    runs = [
        {"status": "measured", "scenario": "steady", "samples": [{"offset_s": 0.01}] * 1000},
        {"status": "measured", "scenario": "seek", "samples": [{"offset_s": 0.2}] * 10},
        {"status": "measured", "scenario": "pause_resume", "samples": [{"offset_s": 0.1}] * 10},
    ]
    combined = combine_sync(runs)
    assert combined["pooled_p95_abs_s"] == 0.01
    assert combined["p95_abs_s"] == 0.2
    assert combined["sync_tolerance_s"] == pytest.approx(0.3)


def test_scenario_requires_an_actual_counter_jump_or_interior_pause() -> None:
    times = np.arange(0, 24, 1 / 60)
    frames = [FrameSignals(int(t * FPS), 48, 48, np.zeros(220)) for t in times]
    capture = Capture(times.tolist(), frames, "test", 60)
    with pytest.raises(ValueError, match="counter jump"):
        sync_measurement(capture, descriptor("sync"), "seek")
    with pytest.raises(ValueError, match="hold an interior"):
        sync_measurement(capture, descriptor("sync"), "pause_resume")
    eof = [FrameSignals(718, 48, 48, np.zeros(220)) for _ in times]
    with pytest.raises(ValueError, match="hold an interior"):
        sync_measurement(
            Capture(times.tolist(), eof, "test", 60), descriptor("sync"), "pause_resume"
        )


def test_seek_into_existing_veil_is_coverage_evidence_not_an_invented_offset() -> None:
    spec = descriptor("sync")
    spec["cues"] = [
        {"id": f"sync_{t}", "t_on": t, "t_off": t + 0.5, "alpha": 0.5, "gray": 0.5}
        for t in SYNC_TIMES
    ]
    times = np.arange(0, 24, 1 / 60)

    def media(t):
        return min(t if t < 2.2 else t + 5.8, 23.99)

    frames = []
    for t in times:
        m = media(t)
        index = int(np.floor(m * FPS + 1e-6))
        pulse = index in {v * FPS for v in SYNC_TIMES}
        veil = any(v <= media(t - 1 / 60) < v + 0.5 for v in SYNC_TIMES)
        alpha = 0.5 if veil else 0
        background = (1 - alpha) * 48 + alpha * 128
        patch = background + ((1 - alpha) * 187 if pulse else 0)
        frames.append(FrameSignals(index, patch, background, np.zeros(220)))
    run = sync_measurement(Capture(times.tolist(), frames, "test", 60), spec, "seek")
    assert len(run["already_veiled_seek_flashes"]) == 1
    assert run["already_veiled_seek_flashes"][0]["media_frame"] == 240
    assert all(s["media_frame"] != 240 for s in run["samples"])
    assert len(run["samples"]) >= 5


def test_compositor_fit_recovers_all_nine_cases_and_refuses_bad_baseline() -> None:
    spec = descriptor("compositing")
    times = np.arange(0, 30, 1 / 60)
    frames = []
    codes = np.arange(16, 236, dtype=np.float64)
    for t in times:
        cue = next((c for c in spec["cues"] if c["t_on"] <= t < c["t_off"]), None)
        output = (
            codes if cue is None else (1 - cue["alpha"]) * codes + cue["alpha"] * cue["gray"] * 255
        )
        frames.append(FrameSignals(int(t * FPS), 48, 48, output))
    capture = Capture(times.tolist(), frames, "test-only", 60)
    result = compositing_measurement(capture, spec)
    assert len(result["cases"]) == 9
    # A perfect RGB blend exposes the old range error independently of fitting.
    assert result["model_passes_two_code_gate"]
    assert result["original_engine_y_max_error_codes"] > 2
    assert result["engine_y_max_error_codes"] < 1
    assert result["max_error_codes"] < 1
    for case in result["cases"]:
        assert case["fit_slope"] == pytest.approx(1 - case["alpha"])
        assert case["fit_intercept"] == pytest.approx(case["alpha"] * case["gray"] * 255)
    bad = [FrameSignals(f.counter, f.patch, f.background, f.ramp + 10) for f in frames]
    with pytest.raises(ValueError, match="baseline"):
        compositing_measurement(Capture(times.tolist(), bad, "test", 60), spec)
