"""Solve, verify, retry once, then publish only full-file verified profiles."""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from nostrobe.decode.cache import FrameCache, load_cache
from nostrobe.detect.pipeline import PROFILES
from nostrobe.domain.models import HazardTrack, UnresolvedSegment
from nostrobe.domain.profiles import ProfileParams, get_profile
from nostrobe.report.html import render
from nostrobe.track import jsonio, webvtt
from nostrobe.track.stats import track_stats
from nostrobe.veil.solver import distortion, solve
from nostrobe.verify.verifier import detect_cached, verify


def analyze_cache(cache: FrameCache, params: Sequence[ProfileParams]) -> list[HazardTrack]:
    detected = detect_cached(cache, [], params)
    tracks: list[HazardTrack] = []
    for profile in params:
        logging.getLogger("nostrobe").info("solving profile=%s", profile.profile)
        events = detected[profile.profile]
        result = solve(cache, events, profile)
        verified = verify(cache, result.cues, profile)
        if not verified.passes:
            # Preserve source events; retry expands coverage around residual evidence.
            repair = [
                e.model_copy(update={"id": f"retry_{i:04d}"})
                for i, e in enumerate(verified.residual_events, 1)
            ]
            retry = solve(cache, [*events, *repair], profile)
            mapping = (
                {
                    e.id: min(events, key=lambda source: abs(source.t_start - e.t_start)).id
                    for e in repair
                }
                if events
                else {}
            )
            if mapping:
                cues = [
                    c.model_copy(update={"covers": sorted({mapping.get(v, v) for v in c.covers})})
                    for c in retry.cues
                ]
                unresolved = [
                    u.model_copy(update={"covers": sorted({mapping.get(v, v) for v in u.covers})})
                    for u in retry.unresolved
                ]
                result = type(result)(cues, unresolved)
                verified = verify(cache, cues, profile)
        unresolved = list(result.unresolved)
        if not verified.passes:
            unresolved.extend(
                UnresolvedSegment(
                    start=e.t_start,
                    end=e.t_end,
                    covers=[],
                    reason="residual fail after final whole-file verification and one retry",
                )
                for e in verified.residual_events
            )
        if unresolved:
            verified = verified.model_copy(update={"passes": False})
        stats = track_stats(events, result.cues, cache.media.duration_s)
        if result.cues:
            cost = distortion(cache, result.cues, 0, cache.media.duration_s)
            fraction = stats.veiled_fraction_of_runtime
            stats = stats.model_copy(
                update={"mean_delta_cd_m2": cost / fraction if fraction else 0}
            )
        tracks.append(
            HazardTrack(
                format="hazardtrack",
                format_version="1.0",
                profile=profile.profile,
                media=cache.media,
                events=events,
                veils=result.cues,
                verifier=verified,
                generated_at=datetime.now(UTC),
                stats=stats,
                unresolved_segments=unresolved,
            )
        )
    return tracks


def analyze(
    path: Path, output: Path, profiles: Sequence[ProfileParams] | None = None
) -> list[HazardTrack]:
    cache = load_cache(path)
    tracks = analyze_cache(cache, profiles or [get_profile(p) for p in PROFILES])
    output.mkdir(parents=True, exist_ok=True)
    for track in tracks:
        stem = f"{track.media.content_id}.{track.profile}"
        json_path = output / f"{stem}.hzt.json"
        vtt_path = output / f"{stem}.hzt.vtt"
        debug_path = output / f"{stem}.unresolved.hzt.json"
        # Remove stale verified artifacts when re-analysis fails for this profile.
        if not track.verifier.passes:
            json_path.unlink(missing_ok=True)
            vtt_path.unlink(missing_ok=True)
            jsonio.write(debug_path, track)
        else:
            jsonio.write(json_path, track)
            vtt_path.write_text(webvtt.serialize(track))
            debug_path.unlink(missing_ok=True)
    (output / "report.html").write_text(render(tracks, cache=cache))
    return tracks
