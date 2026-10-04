"""WCAG 2.2 red helpers; linear-light BT.709 primaries, D65 white point."""

import numpy as np
from numpy.typing import NDArray

from nostrobe.luminance.curve import FloatArray

# BT.709 primaries / D65 to CIE XYZ; W3C CSS Color 4 §10.2.
_RGB_TO_XYZ = np.array(
    [
        [0.4123907993, 0.3575843394, 0.1804807884],
        [0.2126390059, 0.7151686788, 0.0721923154],
        [0.0193308187, 0.1191947798, 0.9505321522],
    ]
)


def _normalized(values: NDArray[np.generic]) -> FloatArray:
    result = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(result)) or np.any((result < 0) | (result > 1)):
        raise ValueError("color values must be finite and normalized to [0, 1]")
    return result


def srgb_to_linear(rgb: NDArray[np.generic]) -> FloatArray:
    """WCAG 2.2 relative-luminance definition (0.04045 breakpoint)."""
    values = _normalized(rgb)
    return np.asarray(
        np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4),
        dtype=np.float64,
    )


def bt709_to_linear(rgb: NDArray[np.generic]) -> FloatArray:
    """Inverse BT.709-6 §1.2 OETF, distinct from sRGB and the display curve."""
    values = _normalized(rgb)
    return np.asarray(
        np.where(values < 0.081, values / 4.5, ((values + 0.099) / 1.099) ** (1 / 0.45)),
        dtype=np.float64,
    )


def rgb24_to_linear(rgb: NDArray[np.uint8]) -> FloatArray:
    """Full-range ffmpeg rgb24 is interpreted as BT.709 nonlinear RGB."""
    return bt709_to_linear(rgb.astype(np.float64) / 255.0)


def red_ratio(linear_rgb: NDArray[np.generic]) -> FloatArray:
    """R/(R+G+B) on linear channels; black defined as zero."""
    values = _normalized(linear_rgb)
    if values.shape[-1] != 3:
        raise ValueError("expected RGB channels on the last axis")
    total = values.sum(axis=-1)
    return np.divide(values[..., 0], total, out=np.zeros_like(total), where=total > 0)


def cie1976_uv(linear_rgb: NDArray[np.generic]) -> FloatArray:
    """CIE 1976 u'=4X/(X+15Y+3Z), v'=9Y/(X+15Y+3Z); black maps to (0,0)."""
    values = _normalized(linear_rgb)
    if values.shape[-1] != 3:
        raise ValueError("expected RGB channels on the last axis")
    xyz = values @ _RGB_TO_XYZ.T
    den = xyz[..., 0] + 15 * xyz[..., 1] + 3 * xyz[..., 2]
    u = np.divide(4 * xyz[..., 0], den, out=np.zeros_like(den), where=den > 0)
    v = np.divide(9 * xyz[..., 1], den, out=np.zeros_like(den), where=den > 0)
    return np.stack((u, v), axis=-1)


def red_transition(before: NDArray[np.generic], after: NDArray[np.generic]) -> NDArray[np.bool_]:
    """WCAG 2.2 flash-threshold Note 3: saturated endpoint AND distance >0.2.

    This classifies one transition; pairing opposing transitions belongs to S2.
    Includes transitions between two saturated-red endpoints.
    """
    saturated = (red_ratio(before) >= 0.8) | (red_ratio(after) >= 0.8)
    distance = np.linalg.norm(cie1976_uv(after) - cie1976_uv(before), axis=-1)
    return np.asarray(saturated & (distance > 0.2), dtype=np.bool_)
