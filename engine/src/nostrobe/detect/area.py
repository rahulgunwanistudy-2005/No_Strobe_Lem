"""Concurrent screen area, BT.1702-3 Annex 1 Guideline 1; local is product policy."""

import numpy as np
from numpy.typing import NDArray

from nostrobe.detect.kernels import local_area
from nostrobe.domain.profiles import ProfileParams


class CountAreas:
    """Share exact per-frame area calculations across profile policies."""

    def __init__(self, counts: NDArray[np.int64]) -> None:
        self.counts = counts
        self._fractions: dict[tuple[int, str], float] = {}
        self._masks: dict[int, NDArray[np.bool_]] = {}
        self._maximum: int | None = None

    @property
    def maximum(self) -> int:
        if self._maximum is None:
            self._maximum = int(self.counts.max())
        return self._maximum

    def mask(self, minimum: int) -> NDArray[np.bool_]:
        if minimum not in self._masks:
            self._masks[minimum] = self.counts >= minimum
        return self._masks[minimum]

    def fraction(self, minimum: int, params: ProfileParams) -> float:
        key = (minimum, params.area_rule)
        if key not in self._fractions:
            self._fractions[key] = area_fraction(self.mask(minimum), params)
        return self._fractions[key]


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
    if mask.all():
        return 1.0
    return local_area(mask, height, width)


def area_fraction(mask: NDArray[np.bool_], params: ProfileParams) -> float:
    if params.area_rule == "global":
        return global_fraction(mask)
    win = (max(1, mask.shape[0] // 3), max(1, mask.shape[1] // 3))
    return max_local_fraction(mask, win)
