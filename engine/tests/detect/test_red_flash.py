import numpy as np
import pytest

from nostrobe.detect.pipeline import detect_arrays
from nostrobe.detect.red_flash import RedFlashDetector
from nostrobe.domain.profiles import get_profile
from nostrobe.luminance.color import cie1976_uv, red_ratio


@pytest.mark.parametrize("fps", (24, 25, 30, 50, 60))
@pytest.mark.parametrize("ratio,expected", [(0.799, False), (0.8, True), (0.801, True)])
def test_saturated_ratio_boundary(fps, ratio, expected):
    t = np.arange(fps * 3) / fps
    colors = np.array([[ratio, 1 - ratio, 0], [0, 0, 1]])
    assert np.linalg.norm(cie1976_uv(colors)[1] - cie1976_uv(colors)[0]) > 0.2
    rgb = colors[(t * 3.5 % 1 >= 0.5).astype(int), None, None, :]
    luma = np.full(rgb.shape[:-1], 100.0)
    events = detect_arrays(luma, t, rgb=rgb)
    for items in events.values():
        assert any(e.kind == "red_flash" and e.severity == "fail" for e in items) == expected


@pytest.mark.parametrize("distance,expected", [(0.199, False), (0.2, False), (0.201, True)])
def test_strict_chromaticity_boundary(monkeypatch, distance, expected):
    # Isolate the exact comparison from RGB->XYZ rounding; the sourced matrix
    # and real color pairs are exercised separately above and in S1.
    def uv(rgb):
        result = np.zeros((*rgb.shape[:-1], 2))
        result[..., 0] = rgb[..., 2] * distance
        return result

    monkeypatch.setattr(
        "nostrobe.detect.red_flash.red_features",
        lambda rgb: (np.moveaxis(uv(rgb), -1, 0), red_ratio(rgb) >= 0.8),
    )
    detector = RedFlashDetector((1, 1))
    count = 0
    for index in range(20):
        color = [1, 0, 0] if index % 2 == 0 else [0, 0, 1]
        counts, _ = detector.update(np.array([[color]], dtype=float), index / 25)
        count = max(count, counts.item())
    assert (count > 6) == expected


def test_red_rule_can_be_disabled():
    from dataclasses import replace

    t = np.arange(75) / 25
    rgb = np.array([[1.0, 0, 0], [0, 0, 1]])[(t * 3.5 % 1 >= 0.5).astype(int), None, None, :]
    events = detect_arrays(
        np.full(rgb.shape[:-1], 100.0),
        t,
        [replace(get_profile("broadcast"), red_rule=False)],
        rgb=rgb,
    )
    assert not events["broadcast"]


@pytest.mark.parametrize("fps", (24, 25, 30, 50, 60))
def test_initial_mid_color_does_not_hide_red_flash(fps):
    colors = np.array([[1.0, 0, 0], [0.8, 0, 0.2], [0.5, 0, 0.5]])
    uv = cie1976_uv(colors)
    assert np.linalg.norm(uv[0] - uv[2]) > 0.2
    assert np.max(np.linalg.norm(uv - uv[1], axis=-1)) < 0.2
    t = np.arange(fps * 3) / fps
    rgb = colors[[0, 2]][(t * 3.5 % 1 >= 0.5).astype(int), None, None, :]
    rgb[0] = colors[1]
    result = detect_arrays(np.full(rgb.shape[:-1], 100.0), t, rgb=rgb)
    for events in result.values():
        assert any(e.kind == "red_flash" and e.severity == "fail" for e in events)
