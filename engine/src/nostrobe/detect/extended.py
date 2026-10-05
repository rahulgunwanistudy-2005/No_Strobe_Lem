"""Ofcom Annex 1 §2: prolonged flashing warning; numeric policy is a product choice."""

from nostrobe.detect.area import CountAreas, area_fraction
from nostrobe.detect.events import FrameEvidence
from nostrobe.detect.zigzag import TIME_EPS, IntArray
from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


class ExtendedDetector:
    def __init__(self, params: ProfileParams) -> None:
        self.params = params
        self._start: float | None = None

    def update(self, counts: IntArray, t: float, areas: CountAreas | None = None) -> FrameEvidence:
        maximum = areas.maximum if areas is not None else int(counts.max())
        if maximum < self.params.extended_changes_per_s:
            self._start = None
            return FrameEvidence(t, None, 0, 0)
        hot = counts >= self.params.extended_changes_per_s
        area = (
            areas.fraction(self.params.extended_changes_per_s, self.params)
            if areas is not None
            else area_fraction(hot, self.params)
        )
        if area > self.params.extended_area:
            if self._start is None:
                self._start = t
        else:
            self._start = None
        active = (
            self._start is not None and t - self._start > self.params.extended_duration_s + TIME_EPS
        )
        return FrameEvidence(t, "warn" if active else None, maximum, area)


def detect_extended(
    frames: FloatArray, timestamps: FloatArray, params: ProfileParams
) -> list[HazardEvent]:
    from nostrobe.detect.pipeline import detect_arrays

    return [
        event
        for event in detect_arrays(frames, timestamps, [params])[params.profile]
        if event.kind == "extended_flashing"
    ]
