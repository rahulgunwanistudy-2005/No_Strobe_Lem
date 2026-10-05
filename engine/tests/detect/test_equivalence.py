"""Optimization must preserve state, counters, strict boundaries and area."""

import numpy as np
import pytest
from reference_numpy import ReferenceChangeDetector, ReferenceRedFlashDetector

from nostrobe.detect.area import CountAreas, area_fraction
from nostrobe.detect.kernels import red_crossings
from nostrobe.detect.red_flash import RedFlashDetector
from nostrobe.detect.zigzag import ChangeDetector, sdr_threshold
from nostrobe.domain.profiles import get_profile


@pytest.mark.parametrize("fps", [24, 25, 30, 50, 60])
@pytest.mark.parametrize("shape", [(1, 1), (9, 12), (90, 160)])
def test_state_and_counter_equivalence(fps, shape):
    rng = np.random.default_rng(571 + fps)
    current = ChangeDetector(shape, sdr_threshold)
    original = ReferenceChangeDetector(shape, sdr_threshold)
    red = RedFlashDetector(shape)
    original_red = ReferenceRedFlashDetector(shape)
    palette = np.array([[0, 0, 0], [1, 0, 0], [0, 0, 1], [0.8, 0.2, 0], [0.5, 0, 0.5]])
    for index in range(2 * fps + 2):
        t = index / fps
        # Mix ramps, noise, sharp crossings and the exact SDR regime edges.
        luma = rng.choice([0, 19, 20, 99, 119, 139, 159, 160, 170, 200], size=shape).astype(float)
        luma[:, ::3] = 100 + 3 * np.sin(index / 3)
        np.testing.assert_array_equal(current.update(luma, t), original.update(luma, t))
        for name in ("anchor", "extreme", "direction", "delta"):
            np.testing.assert_array_equal(getattr(current, name), getattr(original, name))
        np.testing.assert_array_equal(current.history.counts, original.history.counts)
        rgb = palette[rng.integers(0, len(palette), shape)]
        rgb[:, ::3] = rng.random((*rgb[:, ::3].shape,))
        actual_counts = red.update(rgb, t)
        expected_counts = original_red.update(rgb, t)
        for actual, expected in zip(actual_counts, expected_counts, strict=True):
            np.testing.assert_array_equal(actual, expected)
        for name in ("_anchor", "_extreme"):
            np.testing.assert_array_equal(
                getattr(red, name), np.moveaxis(getattr(original_red, name), -1, 0)
            )
        for name in ("_anchor_sat", "_extreme_sat", "_direction"):
            np.testing.assert_array_equal(getattr(red, name), getattr(original_red, name))


def test_norm_rounding_at_strict_boundary():
    rng = np.random.default_rng(291)
    values = rng.uniform(-1, 1, (2, 100_000))
    values[:, :3] = [[np.nextafter(0.2, 0), 0.2, np.nextafter(0.2, 1)], [0, 0, 0]]
    uv = values[:, None, :]
    shape = (1, values.shape[1])
    changes, _ = red_crossings(
        uv,
        np.ones(shape, dtype=bool),
        np.zeros_like(uv),
        np.zeros_like(uv),
        np.ones(shape, dtype=bool),
        np.ones(shape, dtype=bool),
        np.zeros(shape, dtype=np.int64),
    )
    np.testing.assert_array_equal(changes[0], np.linalg.norm(values.T, axis=-1) > 0.2)


def test_shared_area_and_all_borders_match_scalar_windows():
    rng = np.random.default_rng(992)
    for shape in [(1, 1), (9, 12), (90, 160)]:
        counts = rng.integers(0, 15, shape, dtype=np.int64)
        areas = CountAreas(counts)
        for minimum in [3, 4, 5, 7]:
            for profile in ["broadcast", "local", "kids"]:
                params = get_profile(profile)
                mask = counts >= minimum
                value = areas.fraction(minimum, params)
                assert value == area_fraction(mask, params)
                if shape != (90, 160) and params.area_rule == "local":
                    h, w = max(1, shape[0] // 3), max(1, shape[1] // 3)
                    assert value == max(
                        mask[y : y + h, x : x + w].mean()
                        for y in range(shape[0] - h + 1)
                        for x in range(shape[1] - w + 1)
                    )


@pytest.mark.parametrize("shape", [(1, 1), (9, 12), (90, 160)])
def test_paired_histories_match_original_at_irregular_timestamps(shape):
    from reference_numpy import ReferenceFlashCounter

    from nostrobe.detect.rate import FlashCounter

    rng = np.random.default_rng(532)
    current, original = FlashCounter(shape), ReferenceFlashCounter(shape)
    t = 0.0
    for _index in range(240):
        t += rng.choice([1 / 60, 0.02, 0.04, 0.34, 0.36, 0.38, 1.0])
        changes = rng.random(shape) < 0.4
        direction = rng.integers(-1, 2, shape, dtype=np.int8)
        for a, b in zip(
            current.update(changes, direction, t),
            original.update(changes, direction, t),
            strict=True,
        ):
            np.testing.assert_array_equal(a, b)
        for name in (
            "direction",
            "_pending",
            "_lead",
            "_previous_lead",
            "_previous_tail",
            "_previous_counted",
            "_dense_flash",
        ):
            np.testing.assert_array_equal(getattr(current, name), getattr(original, name))
        for window in ("raw", "dense"):
            actual, expected = getattr(current, window), getattr(original, window)
            assert actual._times == expected._times
            for timestamp in expected._times:
                np.testing.assert_array_equal(actual._masks[timestamp], expected._masks[timestamp])


def test_counter_rejects_mismatched_kernel_inputs():
    from nostrobe.detect.rate import FlashCounter

    counter = FlashCounter((9, 12))
    with pytest.raises(ValueError, match="shapes"):
        counter.update(np.ones((9, 12), dtype=bool), np.ones((1, 1), dtype=np.int8), 0)


def test_kernels_use_single_core_and_strict_arithmetic():
    from nostrobe.detect import kernels

    for name in ("sdr_crossings", "red_crossings", "color_features", "local_area", "pair_edges"):
        options = getattr(kernels, name).targetoptions
        assert options["parallel"] is False
        assert options["fastmath"] is False


@pytest.mark.parametrize("limit", [0, 2, 4, 6, 12, 20])
def test_shared_evidence_matches_original(limit):
    from dataclasses import replace

    from reference_numpy import reference_flash_evidence

    from nostrobe.detect.luma_flash import flash_evidence

    rng = np.random.default_rng(890)
    for _ in range(30):
        counts = rng.integers(0, 15, (9, 12), dtype=np.int64)
        deltas = rng.random(counts.shape) * 200
        areas = CountAreas(counts)
        for profile in ("broadcast", "local", "kids"):
            params = replace(get_profile(profile), max_changes_per_s=limit)
            assert flash_evidence(counts, 0.4, params, deltas, areas) == reference_flash_evidence(
                counts, 0.4, params, deltas
            )
