"""Interval-union accuracy and duration-weighted viewing-cost aggregation."""

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel

from nostrobe.domain.models import HazardEvent, HazardTrack
from nostrobe.evaluation.truth import ProfileTruth
from nostrobe.synth.generator import TruthInterval


class Observation(BaseModel):
    suite: str
    name: str
    profile: str
    source_sha256: str
    duration_s: float
    truth: ProfileTruth | None
    events: list[HazardEvent]
    track: HazardTrack | None
    detect_s: float
    analyze_s: float | None
    decode_s: float
    trace: str | None = None


def interval_iou(events: Sequence[HazardEvent], intervals: Sequence[TruthInterval]) -> float:
    points = sorted(
        {t for e in events for t in (e.t_start, e.t_end)}
        | {t for e in intervals for t in (e.t_start, e.t_end)}
    )
    intersection = union = 0.0
    for a, b in zip(points, points[1:], strict=False):
        actual = any(e.t_start <= a and b <= e.t_end for e in events)
        expected = any(e.t_start <= a and b <= e.t_end for e in intervals)
        union += (b - a) * (actual or expected)
        intersection += (b - a) * (actual and expected)
    return intersection / union if union else 1.0


def summarize(rows: Sequence[Observation]) -> dict[str, object]:
    result: dict[str, object] = {}
    for profile in ("broadcast", "local", "kids"):
        selected = [r for r in rows if r.profile == profile and r.truth is not None]
        confusion = dict(tp=0, tn=0, fp=0, fn=0)
        ious = []
        for row in selected:
            assert row.truth is not None
            fails = [e for e in row.events if e.severity == "fail"]
            confusion[
                ("t" if bool(fails) == row.truth.must_fail else "f") + ("p" if bool(fails) else "n")
            ] += 1
            if row.truth.must_fail:
                ious.append(interval_iou(fails, row.truth.intervals))
        tracks = [r.track for r in selected if r.track is not None]
        duration = sum(t.media.duration_s for t in tracks)
        veiled = sum(t.stats.veiled_fraction_of_runtime * t.media.duration_s for t in tracks)
        passed = sum(t.verifier.passes for t in tracks)
        unresolved = sum(len(t.unresolved_segments) for t in tracks)
        accounted = sum(t.verifier.passes or bool(t.unresolved_segments) for t in tracks)
        result[profile] = {
            "confusion": confusion,
            "clips": len(selected),
            "iou_median": float(np.median(ious)) if ious else None,
            "iou_p10": float(np.percentile(ious, 10)) if ious else None,
            "verified_tracks": passed,
            "analyzed_tracks": len(tracks),
            "verifier_pass_rate": passed / len(tracks) if tracks else None,
            "unresolved_segments": unresolved,
            "gate_passes": confusion["fn"] == 0 and accounted == len(tracks),
            "veiled_fraction": veiled / duration if duration else 0,
            "mean_alpha": sum(
                t.stats.mean_alpha * t.stats.veiled_fraction_of_runtime * t.media.duration_s
                for t in tracks
            )
            / veiled
            if veiled
            else 0,
            "mean_delta_cd_m2": sum(
                t.stats.mean_delta_cd_m2 * t.stats.veiled_fraction_of_runtime * t.media.duration_s
                for t in tracks
            )
            / veiled
            if veiled
            else 0,
        }
    return result
