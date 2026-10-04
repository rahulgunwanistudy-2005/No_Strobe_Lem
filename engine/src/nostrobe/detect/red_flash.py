"""WCAG 2.2 flash-threshold Notes 2/3; BT.709 linear RGB cell inputs."""

import math

import numpy as np

from nostrobe.detect.rate import FlashCounter
from nostrobe.detect.zigzag import IntArray
from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.color import cie1976_uv, red_ratio
from nostrobe.luminance.curve import FloatArray


class RedFlashDetector:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        self.shape = shape
        self.rate = FlashCounter(shape, spacing_s)
        self._uv: FloatArray | None = None
        self._saturated = np.zeros(shape, dtype=np.bool_)
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
        direction = np.zeros(self.shape, dtype=np.int8)
        if self._uv is not None:
            displacement = uv - self._uv
            changes = (saturated | self._saturated) & (np.linalg.norm(displacement, axis=-1) > 0.2)
            dominant = np.where(
                np.abs(displacement[..., 0]) >= np.abs(displacement[..., 1]),
                displacement[..., 0],
                displacement[..., 1],
            )
            direction = np.sign(dominant).astype(np.int8)
            self._uv[changes] = uv[changes]
            self._saturated[changes] = saturated[changes]
        else:
            self._uv = uv.copy()
            self._saturated = saturated.copy()
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
