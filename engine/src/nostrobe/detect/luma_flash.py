"""SDR luminance flashes: BT.1702-3 Annex 1 Guideline 1."""

import numpy as np

from nostrobe.detect.area import CountAreas, area_fraction
from nostrobe.detect.events import FrameEvidence
from nostrobe.detect.rate import FlashCounter
from nostrobe.detect.zigzag import ChangeDetector, IntArray, sdr_threshold
from nostrobe.domain.models import HazardEvent, Severity
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


class LumaFlashDetector:
    def __init__(self, shape: tuple[int, int], spacing_s: float = 0.36) -> None:
        # FlashCounter retains every opposing edge needed by the pipeline;
        # the standalone crossing history would duplicate unused timestamps.
        self.change = ChangeDetector(shape, sdr_threshold, keep_history=False)
        self.rate = FlashCounter(shape, spacing_s)
        self.peak_delta = np.zeros(shape)

    def update(self, luminance: FloatArray, t: float) -> tuple[IntArray, IntArray]:
        changes = self.change.update(luminance, t)
        np.copyto(self.peak_delta, self.change.delta, where=changes)
        return self.rate.update(changes, self.change.direction, t)


def flash_evidence(
    counts: IntArray,
    t: float,
    params: ProfileParams,
    deltas: FloatArray | None = None,
    areas: CountAreas | None = None,
) -> FrameEvidence:
    maximum = areas.maximum if areas is not None else int(counts.max())
    if maximum < 0.8 * params.max_changes_per_s:
        return FrameEvidence(t, None, 0, 0)
    hot = (
        areas.mask(params.max_changes_per_s + 1)
        if areas is not None
        else counts > params.max_changes_per_s
    )
    area = (
        areas.fraction(params.max_changes_per_s + 1, params)
        if areas is not None
        else area_fraction(hot, params)
    )
    severity: Severity | None = None
    measured = hot
    if area > params.area_threshold:
        severity = "fail"
    else:
        minimum = int(np.ceil(0.8 * params.max_changes_per_s))
        near = areas.mask(minimum) if areas is not None else counts >= minimum
        near_area = (
            areas.fraction(minimum, params) if areas is not None else area_fraction(near, params)
        )
        if near_area >= 0.8 * params.area_threshold:
            severity, area, measured = "warn", near_area, near
    has_measured = severity == "warn" or maximum > params.max_changes_per_s
    peak_count = maximum if has_measured else 0
    delta = float(deltas[measured].max()) if deltas is not None and has_measured else None
    return FrameEvidence(t, severity, peak_count, area, delta)


def detect_luma(
    frames: FloatArray, timestamps: FloatArray, params: ProfileParams
) -> list[HazardEvent]:
    from nostrobe.detect.pipeline import detect_arrays

    return [
        event
        for event in detect_arrays(frames, timestamps, [params])[params.profile]
        if event.kind == "luma_flash"
    ]
