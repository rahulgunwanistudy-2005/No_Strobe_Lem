import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from nostrobe.luminance.curve import cd_m2_to_code10, code10_to_cd_m2, thr


def test_document_anchors() -> None:
    assert code10_to_cd_m2(np.array([400]))[0] == pytest.approx(20.1, abs=0.3)
    assert code10_to_cd_m2(np.array([863]))[0] == pytest.approx(160.4, abs=0.3)
    np.testing.assert_allclose(code10_to_cd_m2(np.array([64, 940])), [0, 200])


def test_monotonicity_and_footroom() -> None:
    assert np.all(np.diff(code10_to_cd_m2(np.arange(64, 941))) > 0)
    assert np.all(np.diff(code10_to_cd_m2(np.arange(1024))) >= 0)
    np.testing.assert_equal(code10_to_cd_m2(np.array([0, 63, 941, 1023])), [0, 0, 200, 200])


@given(st.lists(st.integers(min_value=64, max_value=940), min_size=1, max_size=50))
def test_vectorized_equals_scalar(codes: list[int]) -> None:
    expected = [float(code10_to_cd_m2(np.array(code))) for code in codes]
    np.testing.assert_allclose(code10_to_cd_m2(np.array(codes)), expected)


def test_threshold_continuity_and_relative_contrast() -> None:
    np.testing.assert_allclose(
        thr(np.array([159.999999, 160, 160.000001])), [20, 20, 20], atol=1e-6
    )
    dark = np.array([160, 170, 200, 1000])
    delta = thr(dark)
    np.testing.assert_allclose(delta / (2 * dark + delta), 1 / 17)


def test_inverse_and_invalid_values() -> None:
    codes = np.arange(64, 941)
    np.testing.assert_allclose(cd_m2_to_code10(code10_to_cd_m2(codes)), codes)
    for value in (-1, 1024, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            code10_to_cd_m2(np.array([value]))
