import numpy as np
import pytest

from nostrobe.luminance.color import (
    bt709_to_linear,
    cie1976_uv,
    red_ratio,
    red_transition,
    srgb_to_linear,
)


def test_transfer_helpers() -> None:
    np.testing.assert_allclose(srgb_to_linear(np.array([0, 0.04045, 1])), [0, 0.04045 / 12.92, 1])
    np.testing.assert_allclose(bt709_to_linear(np.array([0, 0.045, 1])), [0, 0.01, 1])
    assert abs(srgb_to_linear(np.array([0.5]))[0] - bt709_to_linear(np.array([0.5]))[0]) > 0.01


def test_uv_primary_and_white_anchors() -> None:
    np.testing.assert_allclose(cie1976_uv(np.array([1.0, 1.0, 1.0])), [0.19783, 0.46832], atol=1e-5)
    np.testing.assert_allclose(cie1976_uv(np.array([1.0, 0.0, 0.0])), [0.45070, 0.52289], atol=1e-5)
    np.testing.assert_equal(cie1976_uv(np.zeros((2, 3))), np.zeros((2, 2)))


def test_red_endpoints_and_boundaries() -> None:
    colors = np.array([[0.8, 0.2, 0], [0.799, 0.201, 0], [0, 0, 0]])
    np.testing.assert_allclose(red_ratio(colors), [0.8, 0.799, 0])
    red, blue = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
    assert red_transition(red, blue) and red_transition(blue, red)
    assert not red_transition(red, red)
    assert not red_transition(np.array([0.0, 1.0, 0.0]), blue)
    assert red_transition(red, np.zeros(3))  # Defined conservative black convention.
    # Saturation alone does not meet the required chromaticity-distance threshold.
    assert not red_transition(np.array([0.8, 0.2, 0]), np.array([0.8, 0, 0.2]))
    assert red_transition(colors[0], blue)
    assert not red_transition(colors[1], blue)


def test_invalid_color() -> None:
    with pytest.raises(ValueError):
        srgb_to_linear(np.array([1.1]))
