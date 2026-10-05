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
    # Even a perfect RGB fit does not prove the limited-Y simulation is correct.
    assert not result["model_passes_two_code_gate"]
    assert result["engine_y_max_error_codes"] > 2
    assert result["max_error_codes"] == pytest.approx(0)
    for case in result["cases"]:
        assert case["fit_slope"] == pytest.approx(1 - case["alpha"])
        assert case["fit_intercept"] == pytest.approx(case["alpha"] * case["gray"] * 255)
    bad = [FrameSignals(f.counter, f.patch, f.background, f.ramp + 10) for f in frames]
    with pytest.raises(ValueError, match="baseline"):
        compositing_measurement(Capture(times.tolist(), bad, "test", 60), spec)
