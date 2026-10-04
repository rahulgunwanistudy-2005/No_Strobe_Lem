"""Duration-weighted cost, including ramps and a union of overlapping supports."""

from collections import Counter
from collections.abc import Sequence

from nostrobe.domain.models import HazardEvent, TrackStats, VeilCue
from nostrobe.veil.composite import veil_timeline


def track_stats(
    events: Sequence[HazardEvent], cues: Sequence[VeilCue], duration: float
) -> TrackStats:
    points = {0.0, duration}
    for cue in cues:
        points.update(
            max(0.0, min(duration, t))
            for t in (cue.t_on - cue.ramp_in_s, cue.t_on, cue.t_off, cue.t_off + cue.ramp_out_s)
        )
    # Opacity envelope crossings matter when callers supply overlapping cues.
    ordered = sorted(points)
    for a, b in zip(ordered, ordered[1:], strict=False):
        for i, left in enumerate(cues):
            for right in cues[i + 1 :]:
                la, _ = veil_timeline([left], a)
                lb, _ = veil_timeline([left], b)
                ra, _ = veil_timeline([right], a)
                rb, _ = veil_timeline([right], b)
                d0, d1 = la - ra, lb - rb
                if d0 * d1 < 0:
                    points.add(a + (b - a) * d0 / (d0 - d1))
    active = integral = 0.0
    ordered = sorted(points)
    for a, b in zip(ordered, ordered[1:], strict=False):
        alpha, _ = veil_timeline(cues, (a + b) / 2)
        if alpha > 0:
            active += b - a
            integral += alpha * (b - a)
    return TrackStats(
        veiled_fraction_of_runtime=min(1.0, active / duration),
        mean_alpha=integral / active if active else 0.0,
        n_events_by_kind=dict(Counter(e.kind for e in events)),
    )
