"""Bounded, frame-batched timestamp windows for shared per-cell flash counts.

All cells changed in one frame share a PTS. Store that PTS once and retain
its mask instead of scattering it into a large per-cell timestamp array.
"""

import math
from bisect import insort

import numpy as np

from nostrobe.detect.zigzag import TIME_EPS, BoolArray, IntArray
from nostrobe.luminance.curve import FloatArray


class MaskWindow:
    def __init__(self, shape: tuple[int, int], capacity: int = 64) -> None:
        self.counts: IntArray = np.zeros(shape, dtype=np.int64)
        self.capacity = capacity
        self._masks: dict[float, BoolArray] = {}
        self._times: list[float] = []
        # Bound memory even when >1024 different input PTS occur per second.
        self._max_timestamps = 1024

    def expire(self, t: float) -> None:
        while self._times and self._times[0] <= t - 1 + TIME_EPS:
            oldest = self._times.pop(0)
            self.counts -= self._masks.pop(oldest)

    def add(self, mask: BoolArray, times: float | FloatArray) -> None:
        if not mask.any():
            return
        if np.any(mask & (self.counts == self.capacity)):
            raise ValueError("change timestamp capacity exceeded within one second")
        if isinstance(times, (float, int)):
            self._add(mask, float(times))
        else:
            # Retroactive leading/tail edges can differ by cell; batch by
            # frame PTS, never loop over cells.
            for t in np.unique(times[mask]):
                self._add(mask & (times == t), float(t))

    def _add(self, mask: BoolArray, t: float) -> None:
        if not math.isfinite(t):
            raise ValueError("change timestamps must be finite")
        existing = self._masks.get(t)
        if existing is not None:
            if (existing & mask).any():
                raise ValueError("duplicate cell change at one timestamp")
            existing |= mask
        else:
            if len(self._times) >= self._max_timestamps:
                raise ValueError("more than 1024 distinct change timestamps in one second")
            self._masks[t] = mask.copy()
            insort(self._times, t)
        self.counts += mask
