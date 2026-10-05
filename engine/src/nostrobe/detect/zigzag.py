"""Vectorized threshold crossings; BT.1702-3 Annex 1 Guideline 1.

Crossings are not necessarily opposing. FlashCounter coalesces monotone ones.
"""

import math
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from nostrobe.detect.kernels import sdr_crossings
from nostrobe.detect.zigzag_types import BoolArray as BoolArray
from nostrobe.detect.zigzag_types import IntArray as IntArray
from nostrobe.luminance.curve import FloatArray, thr

Threshold = Callable[[FloatArray], FloatArray]
TIME_EPS = 1e-9


def sdr_threshold(dark: FloatArray) -> FloatArray:
    """SDR: >=20 only below 160; the source's relative rule is HDR-only."""
    return np.where(dark < 160, 20.0, np.inf)


class TimestampRing:
    """Per-cell fixed-capacity timestamps, expiring in O(cells) per edge."""

    def __init__(self, shape: tuple[int, int], capacity: int = 64) -> None:
        if capacity < 8 or len(shape) != 2 or min(shape) <= 0:
            raise ValueError("positive 2D shape and capacity >=8 required")
        self.shape = shape
        self.capacity = capacity
        self.timestamps = np.full((capacity, *shape), -np.inf)
        self.counts = np.zeros(shape, dtype=np.int64)
        self._head = np.zeros(shape, dtype=np.int64)
        self._row, self._col = np.indices(shape)
        self._next_expiry = math.inf

    def expire(self, t: float) -> None:
        if t < self._next_expiry - TIME_EPS:
            return
        while True:
            oldest = self.timestamps[self._head, self._row, self._col]
            expired = (self.counts > 0) & (oldest <= t - 1.0 + TIME_EPS)
            if not expired.any():
                self._next_expiry = (
                    float(oldest[self.counts > 0].min()) + 1
                    if (self.counts > 0).any()
                    else math.inf
                )
                return
            self.counts[expired] -= 1
            self._head[expired] = (self._head[expired] + 1) % self.capacity

    def add(self, mask: BoolArray, times: float | FloatArray) -> None:
        if not mask.any():
            return
        if np.any(mask & (self.counts == self.capacity)):
            raise ValueError("change timestamp capacity exceeded within one second")
        slots = (self._head + self.counts) % self.capacity
        rows, cols = np.nonzero(mask)
        values = times if np.isscalar(times) else np.asarray(times)[mask]
        self.timestamps[slots[mask], rows, cols] = values
        self.counts[mask] += 1
        first = (
            float(times)
            if isinstance(times, (float, int))
            else float(np.asarray(times)[mask].min())
        )
        self._next_expiry = min(self._next_expiry, first + 1)


class ChangeDetector:
    """Running extrema and registered anchors; no loops over image cells."""

    def __init__(
        self, shape: tuple[int, int], thr_fn: Threshold = thr, *, keep_history: bool = True
    ) -> None:
        self.shape = shape
        self.thr_fn = thr_fn
        self.history = TimestampRing(shape)
        self._keep_history = keep_history
        self.extreme = np.zeros(shape)
        self.anchor = np.zeros(shape)
        self.direction = np.zeros(shape, dtype=np.int8)
        self.delta = np.zeros(shape)
        self._last_t = -np.inf

    def update(self, luminance: NDArray[np.generic], t: float) -> BoolArray:
        values = np.asarray(luminance, dtype=np.float64)
        if values.shape != self.shape or not (values.min() >= 0 and math.isfinite(values.max())):
            raise ValueError("luminance must be finite, nonnegative and match detector shape")
        if not math.isfinite(t) or t < 0 or t <= self._last_t:
            raise ValueError("timestamps must be finite, nonnegative and strictly increasing")
        initial = not math.isfinite(self._last_t)
        self._last_t = t
        if self._keep_history:
            self.history.expire(t)
        if initial:
            self.extreme[:] = self.anchor[:] = values
            return np.zeros(self.shape, dtype=np.bool_)
        if self.thr_fn is sdr_threshold:
            changes = sdr_crossings(values, self.extreme, self.anchor, self.direction, self.delta)
            if self._keep_history:
                self.history.add(changes, t)
            return changes
        forward = (values - self.extreme) * self.direction >= 0
        reference = np.where(forward, self.anchor, self.extreme)
        # Before the first registered direction, anchor/extreme are the
        # running minimum/maximum. An initial mid-level must not hide a
        # later qualifying peak-to-valley excursion.
        unset = self.direction == 0
        farther_high = np.abs(values - self.extreme) > np.abs(values - self.anchor)
        reference = np.where(unset & farther_high, self.extreme, reference)
        signed = values - reference
        self.delta = np.abs(signed)
        changes = self.delta >= self.thr_fn(np.minimum(values, reference))
        np.copyto(self.direction, np.sign(signed), where=changes, casting="unsafe")
        np.copyto(self.anchor, values, where=changes)
        unset = self.direction == 0
        extend = (forward | changes) & ~unset
        np.copyto(self.extreme, values, where=extend)
        np.minimum(self.anchor, values, out=self.anchor, where=unset)
        np.maximum(self.extreme, values, out=self.extreme, where=unset)
        if self._keep_history:
            self.history.add(changes, t)
        return changes


def qualifying_changes(frames: FloatArray, timestamps: FloatArray) -> FloatArray:
    if frames.ndim != 3 or len(frames) != len(timestamps) or not len(frames):
        raise ValueError("expected nonempty frame/time arrays of equal length")
    detector = ChangeDetector((frames.shape[1], frames.shape[2]), sdr_threshold)
    return np.asarray(
        [detector.update(frame, float(t)) for frame, t in zip(frames, timestamps, strict=True)],
        dtype=np.float64,
    )
