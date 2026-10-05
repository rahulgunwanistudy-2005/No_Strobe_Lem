"""WCAG 2.2 flash-threshold Notes 2/3; BT.709 linear RGB cell inputs."""

import math

import numpy as np

from nostrobe.detect.kernels import red_crossings
from nostrobe.detect.rate import FlashCounter
from nostrobe.detect.zigzag import IntArray
from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.color import red_features
from nostrobe.luminance.curve import FloatArray


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
        uv, saturated = red_features(linear_rgb)
        if self._anchor is None or self._extreme is None:
            changes = np.zeros(self.shape, dtype=np.bool_)
            self._anchor, self._extreme = uv.copy(), uv.copy()
            self._anchor_sat, self._extreme_sat = saturated.copy(), saturated.copy()
            return self.rate.update(changes, self._direction, t)

        changes, direction = red_crossings(
            uv,
            saturated,
            self._anchor,
            self._extreme,
            self._anchor_sat,
            self._extreme_sat,
            self._direction,
        )
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
