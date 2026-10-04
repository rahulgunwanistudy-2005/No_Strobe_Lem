"""Clamped hazard plateaus; ramps may extend beyond the media endpoints."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from nostrobe.domain.models import HazardEvent, VeilCue
from nostrobe.domain.profiles import ProfileParams


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    covers: tuple[str, ...]

    def cue(self, index: int, alpha: float, gray: float, params: ProfileParams) -> VeilCue:
        return VeilCue(
            id=f"veil_{index:04d}",
            t_on=self.start,
            t_off=self.end,
            ramp_in_s=params.min_ramp_s,
            ramp_out_s=params.min_ramp_s,
            alpha=alpha,
            gray=gray,
            covers=list(self.covers),
        )


def segments(
    events: Sequence[HazardEvent], duration: float, params: ProfileParams
) -> list[Segment]:
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be positive and finite")
    selected = sorted(
        (e for e in events if e.severity == "fail" or params.veil_warn),
        key=lambda e: (e.t_start, e.t_end, e.id),
    )
    result: list[Segment] = []
    # Merge ramp supports too, avoiding a gray switch within overlapping ramps.
    gap = max(params.merge_gap_s, 2 * params.min_ramp_s)
    for event in selected:
        start = max(0.0, event.t_start - params.lead_s)
        end = min(duration, event.t_end + params.tail_s)
        if end <= start:
            raise ValueError("event lies outside the media timeline")
        if result and start - result[-1].end <= gap:
            previous = result.pop()
            result.append(
                Segment(previous.start, max(previous.end, end), (*previous.covers, event.id))
            )
        else:
            result.append(Segment(start, end, (event.id,)))
    return result
