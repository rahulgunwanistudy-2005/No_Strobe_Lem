"""Ofcom Annex 1 §2: prolonged flashing warning; numeric policy is a product choice."""

from nostrobe.detect.area import area_fraction
from nostrobe.detect.events import FrameEvidence
from nostrobe.detect.zigzag import TIME_EPS, IntArray
from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


class ExtendedDetector:
    def __init__(self, params: ProfileParams) -> None:
        self.params = params
        self._start: float | None = None

    def update(self, counts: IntArray, t: float) -> FrameEvidence:
        if counts.max() < self.params.extended_changes_per_s:
            self._start = None
            return FrameEvidence(t, None, 0, 0)
        hot = counts >= self.params.extended_changes_per_s
        area = area_fraction(hot, self.params)
        if area > self.params.extended_area:
            if self._start is None:
                self._start = t
        else:
            self._start = None
        active = (
            self._start is not None and t - self._start > self.params.extended_duration_s + TIME_EPS
        )
        return FrameEvidence(
            t, "warn" if active else None, int(counts[hot].max()) if hot.any() else 0, area
        )


def detect_extended(
    frames: FloatArray, timestamps: FloatArray, params: ProfileParams
) -> list[HazardEvent]:
    from nostrobe.detect.pipeline import detect_arrays

    return [
        event
        for event in detect_arrays(frames, timestamps, [params])[params.profile]
        if event.kind == "extended_flashing"
    ]
