"""Streaming frame evidence to intervals; merge without dropping any events."""

import math
from dataclasses import dataclass

from nostrobe.domain.models import HazardEvent, HazardKind, Severity


@dataclass(frozen=True)
class FrameEvidence:
    t: float
    severity: Severity | None
    changes: int
    area: float
    delta: float | None = None


class EventBuilder:
    """Intervals end at the next frame PTS, including variable-rate video."""

    def __init__(self, kind: HazardKind, merge_gap_s: float) -> None:
        self.kind = kind
        self.merge_gap_s = merge_gap_s
        self.events: list[HazardEvent] = []
        self._active: HazardEvent | None = None
        self._last_t = -math.inf

    def update(self, evidence: FrameEvidence) -> None:
        if evidence.t <= self._last_t:
            raise ValueError("event timestamps must be strictly increasing")
        self._last_t = evidence.t
        if self._active is not None:
            self._active = self._active.model_copy(update={"t_end": evidence.t})
        if self._active is not None and evidence.severity != self._active.severity:
            self.events.append(self._active)
            self._active = None
        if evidence.severity is None:
            return
        if self._active is None:
            self._active = HazardEvent(
                id="pending",
                kind=self.kind,
                severity=evidence.severity,
                t_start=evidence.t,
                t_end=math.nextafter(evidence.t, math.inf),
                peak_changes_per_s=evidence.changes,
                peak_area_fraction=evidence.area,
                peak_delta_cd_m2=evidence.delta,
                regime="red" if self.kind == "red_flash" else "absolute",
            )
        else:
            self._active = self._active.model_copy(
                update={
                    "peak_changes_per_s": max(self._active.peak_changes_per_s, evidence.changes),
                    "peak_area_fraction": max(self._active.peak_area_fraction, evidence.area),
                    "peak_delta_cd_m2": _peak(self._active.peak_delta_cd_m2, evidence.delta),
                }
            )

    def finish(self, end: float) -> list[HazardEvent]:
        if end <= self._last_t:
            raise ValueError("media end must follow the last frame")
        if self._active is not None:
            self.events.append(self._active.model_copy(update={"t_end": end}))
            self._active = None
        return merge_events(self.events, self.merge_gap_s)


def _peak(a: float | None, b: float | None) -> float | None:
    values = [v for v in (a, b) if v is not None]
    return max(values) if values else None


def merge_events(events: list[HazardEvent], merge_gap_s: float) -> list[HazardEvent]:
    if not math.isfinite(merge_gap_s) or merge_gap_s < 0:
        raise ValueError("merge gap must be finite and nonnegative")
    grouped: dict[tuple[HazardKind, Severity, str], list[HazardEvent]] = {}
    for event in events:
        grouped.setdefault((event.kind, event.severity, event.regime), []).append(event)
    result: list[HazardEvent] = []
    for group in grouped.values():
        merged: list[HazardEvent] = []
        for event in sorted(group, key=lambda item: (item.t_start, item.t_end)):
            if merged and event.t_start - merged[-1].t_end < merge_gap_s:
                previous = merged[-1]
                merged[-1] = previous.model_copy(
                    update={
                        "t_end": max(previous.t_end, event.t_end),
                        "peak_changes_per_s": max(
                            previous.peak_changes_per_s, event.peak_changes_per_s
                        ),
                        "peak_area_fraction": max(
                            previous.peak_area_fraction, event.peak_area_fraction
                        ),
                        "peak_delta_cd_m2": _peak(
                            previous.peak_delta_cd_m2, event.peak_delta_cd_m2
                        ),
                    }
                )
            else:
                merged.append(event)
        result.extend(merged)
    result.sort(key=lambda item: (item.t_start, item.kind, item.severity))
    return [
        event.model_copy(update={"id": f"evt_{index:04d}"}) for index, event in enumerate(result, 1)
    ]
