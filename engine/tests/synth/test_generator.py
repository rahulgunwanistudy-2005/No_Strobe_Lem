from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from nostrobe.synth.generator import ClipSpec, analytic_truth, encode, iter_frames, smoke_specs


def test_smoke_truth_boundaries_and_isolated_flashes() -> None:
    specs = smoke_specs()
    labels = {spec.name: analytic_truth(spec).label for spec in specs}
    for name in (
        "rate_3",
        "area_24",
        "delta_19",
        "flat",
        "moving_bar",
        "lightning",
        "isolated_1",
        "isolated_2",
        "isolated_3",
    ):
        assert labels[name] == "must_pass"
    for name in (
        "rate_3_5",
        "area_26",
        "delta_21",
        "tiles_26",
        "red_blue",
        "police",
        "camera_burst",
    ):
        assert labels[name] == "must_fail"
    for spec in specs:
        truth = analytic_truth(spec)
        for interval in truth.expected_intervals:
            assert 0 <= interval.t_start < interval.t_end <= spec.n_frames / spec.fps


def test_seeded_tiles_are_reproducible() -> None:
    spec = ClipSpec("tiles", "regional_tiles", area=0.26, duration_s=0.3)
    first, second = list(iter_frames(spec)), list(iter_frames(spec))
    assert all(np.array_equal(a, b) for a, b in zip(first, second, strict=True))
    other = list(iter_frames(replace(spec, seed=8)))
    assert any(not np.array_equal(a, b) for a, b in zip(first, other, strict=True))
    assert analytic_truth(spec).measured_area_fraction == pytest.approx(0.26, abs=1e-4)


@pytest.mark.parametrize("fps", [24, 25, 30, 50, 60])
def test_rate_generalization(fps: int) -> None:
    assert analytic_truth(ClipSpec("flash", "full_flash", fps=fps)).label == "must_fail"


def test_safety_prefix_and_parameter_validation(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="HAZARD_"):
        encode(tmp_path / "unsafe.mp4", ClipSpec("test", "flat"))
    for args in (
        {"width": 31},
        {"rate": 20},
        {"area": 1.1},
        {"duty": 0},
        {"name": "../escape"},
        {"dark_cd_m2": 170, "delta_cd_m2": 60},
    ):
        with pytest.raises(ValueError):
            ClipSpec(**({"name": "test", "primitive": "full_flash"} | args))
