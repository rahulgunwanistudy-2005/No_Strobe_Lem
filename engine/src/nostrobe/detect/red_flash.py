"""WCAG 2.2 flash-threshold Notes 2/3; BT.709 linear RGB cell inputs."""

import math

import numpy as np

from nostrobe.detect.rate import FlashCounter
from nostrobe.detect.zigzag import IntArray
from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.color import cie1976_uv, red_ratio
from nostrobe.luminance.curve import FloatArray


def _direction(displacement: FloatArray) -> IntArray:
    dominant = np.where(
        np.abs(displacement[..., 0]) >= np.abs(displacement[..., 1]),
        displacement[..., 0],
        displacement[..., 1],
    )
    return np.sign(dominant).astype(np.int64)


class RedFlashDetector:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        self.shape = shape
        self.rate = FlashCounter(shape, spacing_s)
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


def detect_red(
    frames: FloatArray, timestamps: FloatArray, params: ProfileParams
) -> list[HazardEvent]:
    from nostrobe.detect.pipeline import detect_arrays

    luma = np.zeros(frames.shape[:-1])
    return [
        event
        for event in detect_arrays(luma, timestamps, [params], frames)[params.profile]
        if event.kind == "red_flash"
    ]
