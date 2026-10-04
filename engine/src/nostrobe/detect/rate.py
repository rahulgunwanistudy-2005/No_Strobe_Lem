"""Opposing transitions and spacing; BT.1702-3 Annex 1 Guideline 1.

The >6-change convention and fixed 360 ms are documented product choices.
"""

import numpy as np
from numpy.typing import NDArray

from nostrobe.detect.zigzag import TIME_EPS, BoolArray, IntArray, TimestampRing


class FlashCounter:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        self.raw = TimestampRing(shape)
        self.dense = TimestampRing(shape)
        self.spacing_s = spacing_s
        self.direction = np.zeros(shape, dtype=np.int8)
        self._pending = np.zeros(shape, dtype=np.bool_)
        self._lead = np.full(shape, -np.inf)
        self._previous_lead = np.full(shape, -np.inf)
        self._previous_tail = np.full(shape, -np.inf)
        self._previous_counted = np.zeros(shape, dtype=np.bool_)
        self._dense_flash = np.zeros(shape, dtype=np.bool_)

    def update(
        self, changes: BoolArray, direction: NDArray[np.signedinteger], t: float
    ) -> tuple[IntArray, IntArray]:
        self.raw.expire(t)
        self.dense.expire(t)
        edges = changes & (direction != 0) & (direction != self.direction)
        if not edges.any():
            return self.dense.counts, self.raw.counts
        leading = edges & ~self._pending
        trailing = edges & self._pending
        # The second leading edge establishes dense flashing, including the
        # immediately preceding flash; slow flashes contribute only to raw.
        close = leading & (t - self._previous_lead < self.spacing_s - TIME_EPS)
        retro = close & ~self._previous_counted
        self.dense.add(retro & (self._previous_lead > t - 1 + TIME_EPS), self._previous_lead)
        self.dense.add(retro & (self._previous_tail > t - 1 + TIME_EPS), self._previous_tail)
        self._dense_flash[leading] = close[leading]
        self._lead[leading] = t
        self.dense.add(close | (trailing & self._dense_flash), t)
        self._previous_lead[trailing] = self._lead[trailing]
        self._previous_tail[trailing] = t
        self._previous_counted[trailing] = self._dense_flash[trailing]
        self._pending[leading] = True
        self._pending[trailing] = False
        self.direction[edges] = direction[edges]
        self.raw.add(edges, t)
        return self.dense.counts, self.raw.counts
