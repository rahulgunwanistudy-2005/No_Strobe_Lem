"""BT.1702-3 (11/2023), Annex 2, Table 1, printed p.7; SDR only."""

from importlib.resources import files

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
with files(__package__).joinpath("bt1702_sdr_curve.csv").open("r") as _source:
    _table = np.loadtxt(_source, delimiter=",", comments="#", skiprows=4)


def code10_to_cd_m2(code: NDArray[np.generic]) -> FloatArray:
    """Piecewise-linear table interpolation; clamp foot/headroom to black/white."""
    values = np.asarray(code, dtype=np.float64)
    if not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 1023)):
        raise ValueError("10-bit codes must be finite and in [0, 1023]")
    return np.asarray(np.interp(values, _table[:, 0], _table[:, 1]), dtype=np.float64)


def cd_m2_to_code10(luminance: NDArray[np.generic]) -> FloatArray:
    """Inverse of the sourced SDR table for synthesis (0..200 cd/m²)."""
    values = np.asarray(luminance, dtype=np.float64)
    if not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 200)):
        raise ValueError("SDR luminance must be finite and in [0, 200]")
    return np.asarray(np.interp(values, _table[:, 1], _table[:, 0]), dtype=np.float64)


def thr(dark: NDArray[np.generic]) -> FloatArray:
    """Bible's continuous boundary; BT.1702-3 Annex 1 Note 6, HDR above 160."""
    values = np.asarray(dark, dtype=np.float64)
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("dark luminance must be finite and nonnegative")
    return np.asarray(np.maximum(20.0, values / 8.0), dtype=np.float64)
