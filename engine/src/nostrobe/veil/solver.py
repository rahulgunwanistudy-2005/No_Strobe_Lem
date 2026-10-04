"""Deterministic minimum-distortion grid search with conservative local checks."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from nostrobe.decode.cache import FrameCache
from nostrobe.domain.models import HazardEvent, UnresolvedSegment, VeilCue
from nostrobe.domain.profiles import ProfileParams
from nostrobe.veil.composite import veil_timeline
from nostrobe.veil.segments import Segment, segments
from nostrobe.verify.verifier import verify


@dataclass(frozen=True)
class SolveResult:
    cues: list[VeilCue]
    unresolved: list[UnresolvedSegment]


def distortion(cache: FrameCache, cues: Sequence[VeilCue], start: float, end: float) -> float:
    total = weight = 0.0
    times = cache.timestamps
    for frame, t in cache.samples(start, end):
        index = int(np.searchsorted(times, t))
        next_t = float(times[index + 1]) if index + 1 < len(times) else cache.media.duration_s
        dt = max(0.0, min(end, next_t) - max(start, t))
        alpha, gray = veil_timeline(cues, t)
        before, _ = cache.cells(frame)
        after, _ = cache.cells(frame, alpha, gray)
        total += float(np.abs(after - before).mean()) * dt
        weight += dt
    return total / weight if weight else 0.0


def _solve_segment(
    cache: FrameCache, segment: Segment, index: int, params: ProfileParams
) -> tuple[VeilCue, UnresolvedSegment | None]:
    support = (
        max(0.0, segment.start - params.min_ramp_s),
        min(cache.media.duration_s, segment.end + params.min_ramp_s),
    )
    context = (max(0.0, support[0] - 1.5), min(cache.media.duration_s, support[1] + 1.5))
    candidates: list[tuple[float, float, float, VeilCue]] = []
    grid = sorted(
        {
            0.0,
            params.max_alpha,
            *(float(v) for v in np.arange(params.alpha_step, params.max_alpha, params.alpha_step)),
        }
    )
    for gray in params.gray_candidates:
        previous = 0.0
        for alpha in grid:
            cue = segment.cue(index, alpha, gray, params)
            if verify(
                cache,
                [cue],
                params,
                bounds=context,
                reject_warnings=params.veil_warn,
                stop_on_failure=True,
            ).passes:
                low, high = previous, alpha
                while high - low > 0.005 + 1e-12:
                    middle = (low + high) / 2
                    if verify(
                        cache,
                        [segment.cue(index, middle, gray, params)],
                        params,
                        bounds=context,
                        reject_warnings=params.veil_warn,
                        stop_on_failure=True,
                    ).passes:
                        high = middle
                    else:
                        low = middle
                cue = segment.cue(index, high, gray, params)
                cost = distortion(cache, [cue], *support)
                candidates.append((cost, high, gray, cue))
                break
            previous = alpha
    if candidates:
        return min(candidates, key=lambda item: item[:3])[3], None
    fallback = [
        segment.cue(index, params.max_alpha, gray, params) for gray in params.gray_candidates
    ]
    cue = min(fallback, key=lambda c: (distortion(cache, [c], *support), c.alpha, c.gray))
    return cue, UnresolvedSegment(
        start=segment.start,
        end=segment.end,
        covers=list(segment.covers),
        reason="no candidate passes all sync offsets at or below max_alpha",
    )


def solve(cache: FrameCache, events: list[HazardEvent], params: ProfileParams) -> SolveResult:
    cues: list[VeilCue] = []
    unresolved: list[UnresolvedSegment] = []
    for index, segment in enumerate(segments(events, cache.media.duration_s, params), 1):
        cue, failure = _solve_segment(cache, segment, index, params)
        # Zero-alpha candidates are valid for warnings; omit their empty veils.
        if cue.alpha > 0:
            cues.append(cue)
        if failure is not None:
            unresolved.append(failure)
    return SolveResult(cues, unresolved)
