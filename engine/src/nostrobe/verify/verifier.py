"""Full-detector closed loop with shifted veil timelines and retained ramps."""

import math
from collections.abc import Sequence
from pathlib import Path

from nostrobe import __version__
from nostrobe.decode.cache import FrameCache, load_cache
from nostrobe.detect.events import merge_events
from nostrobe.detect.pipeline import DetectionPipeline
from nostrobe.domain.models import HazardEvent, VeilCue, VerifierResult
from nostrobe.domain.profiles import ProfileParams, get_profile
from nostrobe.veil.composite import veil_timeline


def detect_cached(
    cache: FrameCache,
    cues: Sequence[VeilCue],
    params: Sequence[ProfileParams],
    offset: float = 0,
    bounds: tuple[float, float] | None = None,
    *,
    stop_on_failure: bool = False,
    reject_warnings: bool = False,
) -> dict[str, list[HazardEvent]]:
    start, end = bounds or (0, cache.media.duration_s)
    shape = cache.shape(start, end)
    pipeline = DetectionPipeline(shape, params)
    last: float | None = None
    for frame, t in cache.samples(start, end):
        alpha, gray = veil_timeline(cues, t - offset)
        frame = frame[: shape[0] * 4, : shape[1] * 4]
        luma, rgb = cache.cells(frame, alpha, gray)
        pipeline.update(luma, rgb, t)
        last = t
        if stop_on_failure and any(
            b.has_evidence(reject_warnings)
            for group in pipeline.builders.values()
            for b in group.values()
        ):
            end = math.nextafter(t, math.inf)
            break
    if last is None:
        raise ValueError("verification interval contains no frames")
    return {
        str(key): value
        for key, value in pipeline.finish(max(end, math.nextafter(last, math.inf))).items()
    }


def verify(
    path: Path | FrameCache,
    cues: Sequence[VeilCue],
    profile: str | ProfileParams = "broadcast",
    offsets: Sequence[float] | None = None,
    *,
    bounds: tuple[float, float] | None = None,
    reject_warnings: bool = False,
    stop_on_failure: bool = False,
) -> VerifierResult:
    cache = load_cache(path) if isinstance(path, Path) else path
    params = get_profile(profile) if isinstance(profile, str) else profile
    checked = list(
        offsets if offsets is not None else (-params.sync_tolerance_s, 0.0, params.sync_tolerance_s)
    )
    if not checked or not all(math.isfinite(v) for v in checked):
        raise ValueError("verification requires finite nonempty offsets")
    residual: list[HazardEvent] = []
    for offset in checked if cues else checked[:1]:
        events = detect_cached(
            cache,
            cues,
            [params],
            offset,
            bounds,
            stop_on_failure=stop_on_failure,
            reject_warnings=reject_warnings,
        )[params.profile]
        residual.extend(e for e in events if e.severity == "fail" or reject_warnings)
        if residual and stop_on_failure:
            checked = checked[: checked.index(offset) + 1]
            break
    residual = merge_events(residual, params.merge_gap_s)
    return VerifierResult(
        passes=not residual,
        offsets_checked_s=checked,
        residual_events=residual,
        engine_version=__version__,
        params_hash=params.params_hash(),
    )
