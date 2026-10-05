"""Frozen pre-optimization NumPy reference from dd980e5 for differential tests."""

import math
from bisect import insort

import numpy as np
from numpy.typing import NDArray

from nostrobe.detect.area import area_fraction
from nostrobe.detect.events import FrameEvidence
from nostrobe.detect.zigzag import TIME_EPS, BoolArray, IntArray, Threshold, TimestampRing
from nostrobe.domain.models import Severity
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray, thr


def _normalized(values: NDArray[np.generic]) -> FloatArray:
    result = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(result)) or np.any((result < 0) | (result > 1)):
        raise ValueError("color values must be finite and normalized to [0, 1]")
    return result


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


_RGB_TO_XYZ = np.array(
    [
        [0.4123907993, 0.3575843394, 0.1804807884],
        [0.2126390059, 0.7151686788, 0.0721923154],
        [0.0193308187, 0.1191947798, 0.9505321522],
    ]
)


class ReferenceChangeDetector:
    """Running extrema and registered anchors; no loops over image cells."""

    def __init__(self, shape: tuple[int, int], thr_fn: Threshold = thr) -> None:
        self.shape = shape
        self.thr_fn = thr_fn
        self.history = TimestampRing(shape)
        self.extreme = np.zeros(shape)
        self.anchor = np.zeros(shape)
        self.direction = np.zeros(shape, dtype=np.int8)
        self.delta = np.zeros(shape)
        self._last_t = -np.inf

    def update(self, luminance: NDArray[np.generic], t: float) -> BoolArray:
        values = np.asarray(luminance, dtype=np.float64)
        if values.shape != self.shape or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("luminance must be finite, nonnegative and match detector shape")
        if not math.isfinite(t) or t < 0 or t <= self._last_t:
            raise ValueError("timestamps must be finite, nonnegative and strictly increasing")
        initial = not math.isfinite(self._last_t)
        self._last_t = t
        self.history.expire(t)
        if initial:
            self.extreme[:] = self.anchor[:] = values
            return np.zeros(self.shape, dtype=np.bool_)
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
        self.direction[changes] = np.sign(signed[changes]).astype(np.int8)
        self.anchor[changes] = values[changes]
        unset = self.direction == 0
        extend = (forward | changes) & ~unset
        self.extreme[extend] = values[extend]
        self.anchor[unset] = np.minimum(self.anchor[unset], values[unset])
        self.extreme[unset] = np.maximum(self.extreme[unset], values[unset])
        self.history.add(changes, t)
        return changes


def _direction(displacement: FloatArray) -> IntArray:
    dominant = np.where(
        np.abs(displacement[..., 0]) >= np.abs(displacement[..., 1]),
        displacement[..., 0],
        displacement[..., 1],
    )
    return np.sign(dominant).astype(np.int64)


class ReferenceMaskWindow:
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


class ReferenceFlashCounter:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        self.raw = ReferenceMaskWindow(shape)
        self.dense = ReferenceMaskWindow(shape)
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


class ReferenceRedFlashDetector:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        self.shape = shape
        self.rate = ReferenceFlashCounter(shape, spacing_s)
        self._anchor: FloatArray | None = None
        self._extreme: FloatArray | None = None
        self._anchor_sat = np.zeros(shape, dtype=np.bool_)
        self._extreme_sat = np.zeros(shape, dtype=np.bool_)
        self._direction = np.zeros(shape, dtype=np.int64)
        self._last_t = -math.inf

    def update(self, linear_rgb: FloatArray, t: float) -> tuple[IntArray, IntArray]:
        if linear_rgb.shape != (*self.shape, 3):
            raise ValueError("RGB cell shape must match the detector")
        if not math.isfinite(t) or t < 0 or t <= self._last_t:
            raise ValueError("timestamps must be finite, nonnegative and strictly increasing")
        self._last_t = t
        uv = cie1976_uv(linear_rgb)
        saturated = red_ratio(linear_rgb) >= 0.8
        changes = np.zeros(self.shape, dtype=np.bool_)
        if self._anchor is None or self._extreme is None:
            self._anchor, self._extreme = uv.copy(), uv.copy()
            self._anchor_sat, self._extreme_sat = saturated.copy(), saturated.copy()
            return self.rate.update(changes, self._direction, t)

        to_anchor, to_extreme = uv - self._anchor, uv - self._extreme
        anchor_distance = np.linalg.norm(to_anchor, axis=-1)
        extreme_distance = np.linalg.norm(to_extreme, axis=-1)
        step = _direction(to_extreme)
        forward = (step == self._direction) | (step == 0)
        unset = self._direction == 0
        use_extreme = np.where(unset, extreme_distance > anchor_distance, ~forward)
        displacement = np.where(use_extreme[..., None], to_extreme, to_anchor)
        reference_sat = np.where(use_extreme, self._extreme_sat, self._anchor_sat)
        distance = np.where(use_extreme, extreme_distance, anchor_distance)
        changes = (saturated | reference_sat) & (distance > 0.2)
        direction = _direction(displacement)
        # Until the first qualified change, retain two observed endpoints of
        # a widening excursion. Both UV coordinates and saturation belong to
        # actual observed colors, not constructed componentwise extrema.
        span = np.linalg.norm(self._extreme - self._anchor, axis=-1)
        grow_anchor = unset & ~changes & (extreme_distance > span) & use_extreme
        grow_extreme = unset & ~changes & (anchor_distance > span) & ~use_extreme
        self._anchor[grow_anchor] = uv[grow_anchor]
        self._anchor_sat[grow_anchor] = saturated[grow_anchor]
        self._extreme[grow_extreme] = uv[grow_extreme]
        self._extreme_sat[grow_extreme] = saturated[grow_extreme]
        self._anchor[changes] = uv[changes]
        self._anchor_sat[changes] = saturated[changes]
        extend = (forward & ~unset) | changes
        self._extreme[extend] = uv[extend]
        self._extreme_sat[extend] = saturated[extend]
        self._direction[changes] = direction[changes]
        return self.rate.update(changes, direction, t)


def reference_flash_evidence(
    counts: IntArray, t: float, params: ProfileParams, deltas: FloatArray | None = None
) -> FrameEvidence:
    if counts.max() < 0.8 * params.max_changes_per_s:
        return FrameEvidence(t, None, 0, 0)
    hot = counts > params.max_changes_per_s
    area = area_fraction(hot, params)
    severity: Severity | None = None
    measured = hot
    if area > params.area_threshold:
        severity = "fail"
    else:
        near = counts >= 0.8 * params.max_changes_per_s
        near_area = area_fraction(near, params)
        if near_area >= 0.8 * params.area_threshold:
            severity, area, measured = "warn", near_area, near
    peak_count = int(counts[measured].max()) if measured.any() else 0
    delta = float(deltas[measured].max()) if deltas is not None and measured.any() else None
    return FrameEvidence(t, severity, peak_count, area, delta)
