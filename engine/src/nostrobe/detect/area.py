"""Concurrent screen area, BT.1702-3 Annex 1 Guideline 1; local is product policy."""

import numpy as np
from numpy.typing import NDArray

from nostrobe.domain.profiles import ProfileParams


def _mask(mask: NDArray[np.bool_]) -> None:
    if mask.ndim != 2 or not mask.size or mask.dtype != np.bool_:
        raise ValueError("expected a nonempty 2D boolean mask")


def global_fraction(mask: NDArray[np.bool_]) -> float:
    _mask(mask)
    return float(np.count_nonzero(mask) / mask.size)


def max_local_fraction(mask: NDArray[np.bool_], win: tuple[int, int] = (30, 53)) -> float:
    """Maximum hot fraction over every valid window, including all borders."""
    _mask(mask)
    height, width = win
    if min(win) <= 0 or height > mask.shape[0] or width > mask.shape[1]:
        raise ValueError("window must be positive and fit within the mask")
    if not mask.any():
        return 0.0
    table = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), dtype=np.int64)
    table[1:, 1:] = mask.cumsum(axis=0, dtype=np.int64).cumsum(axis=1)
    sums = table[height:, width:] - table[:-height, width:]
    sums -= table[height:, :-width] - table[:-height, :-width]
    return float(sums.max() / (height * width))


def area_fraction(mask: NDArray[np.bool_], params: ProfileParams) -> float:
    if params.area_rule == "global":
        return global_fraction(mask)
    win = (max(1, mask.shape[0] // 3), max(1, mask.shape[1] // 3))
    return max_local_fraction(mask, win)
