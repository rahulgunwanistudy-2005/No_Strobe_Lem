"""Opposing transitions and spacing; BT.1702-3 Annex 1 Guideline 1.

The >6-change convention and fixed 360 ms are documented product choices.
"""

import numpy as np
from numpy.typing import NDArray

from nostrobe.detect.kernels import pair_edges
from nostrobe.detect.window import MaskWindow
from nostrobe.detect.zigzag import BoolArray, IntArray


class FlashCounter:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        self.raw = MaskWindow(shape)
        self.dense = MaskWindow(shape)
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
        if changes.shape != self.raw.counts.shape or direction.shape != changes.shape:
            raise ValueError("change and direction shapes must match the counter")
        self.raw.expire(t)
        self.dense.expire(t)
        if not changes.any():
            return self.dense.counts, self.raw.counts
        edges, retro_lead, retro_tail, dense = pair_edges(
            changes,
            direction,
            t,
            self.spacing_s,
            self.direction,
            self._pending,
            self._lead,
            self._previous_lead,
            self._previous_tail,
            self._previous_counted,
            self._dense_flash,
        )
        self.dense.add(retro_lead, self._previous_lead)
        self.dense.add(retro_tail, self._previous_tail)
        self.dense.add(dense, t)
        self.raw.add(edges, t)
        return self.dense.counts, self.raw.counts
