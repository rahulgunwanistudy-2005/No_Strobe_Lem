"""One media/frame pass, shared change detection, per-profile area and events."""

from collections.abc import Generator, Sequence
from contextlib import closing
from pathlib import Path

import numpy as np

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import block_mean, iter_analysis, probe, to_cells
from nostrobe.detect.events import EventBuilder, merge_events
from nostrobe.detect.extended import ExtendedDetector
from nostrobe.detect.luma_flash import LumaFlashDetector, flash_evidence
from nostrobe.detect.red_flash import RedFlashDetector
from nostrobe.domain.models import HazardEvent, HazardKind, ProfileId
from nostrobe.domain.profiles import ProfileParams, get_profile
from nostrobe.errors import DecodeError
from nostrobe.luminance.color import rgb24_to_linear
from nostrobe.luminance.curve import FloatArray

PROFILES: tuple[ProfileId, ...] = ("broadcast", "local", "kids")
_KINDS: tuple[HazardKind, ...] = ("luma_flash", "red_flash", "extended_flashing")
_RGB_LUT = rgb24_to_linear(np.arange(256, dtype=np.uint8))


class DetectionPipeline:
    def __init__(self, shape: tuple[int, int], profiles: Sequence[ProfileParams]) -> None:
        if not profiles or len({p.profile for p in profiles}) != len(profiles):
            raise ValueError("profiles must be nonempty and unique")
        if len({p.leading_edge_spacing_s for p in profiles}) != 1:
            raise ValueError("shared detectors require the same spacing policy")
        self.profiles = tuple(profiles)
        self.luma = LumaFlashDetector(shape, profiles[0].leading_edge_spacing_s)
        self.red = RedFlashDetector(shape, profiles[0].leading_edge_spacing_s)
        self.builders = {
            p.profile: {kind: EventBuilder(kind, p.merge_gap_s) for kind in _KINDS}
            for p in profiles
        }
        self.extended = {p.profile: ExtendedDetector(p) for p in profiles}

    def update(self, luminance: FloatArray, rgb: FloatArray | None, t: float) -> None:
        counts, raw = self.luma.update(luminance, t)
        red_counts, red_raw = (
            self.red.update(rgb, t)
            if rgb is not None
            else (np.zeros_like(counts), np.zeros_like(raw))
        )
        for params in self.profiles:
            builders = self.builders[params.profile]
            builders["luma_flash"].update(flash_evidence(counts, t, params, self.luma.peak_delta))
            if params.red_rule:
                builders["red_flash"].update(flash_evidence(red_counts, t, params))
            builders["extended_flashing"].update(
                self.extended[params.profile].update(
                    np.maximum(raw, red_raw) if params.red_rule else raw, t
                )
            )

    def finish(self, end: float) -> dict[ProfileId, list[HazardEvent]]:
        return {
            p.profile: merge_events(
                [
                    event
                    for builder in self.builders[p.profile].values()
                    for event in builder.finish(end)
                ],
                p.merge_gap_s,
            )
            for p in self.profiles
        }


def detect_arrays(
    frames: FloatArray,
    timestamps: FloatArray,
    profiles: Sequence[ProfileParams] | None = None,
    rgb: FloatArray | None = None,
    *,
    end_s: float | None = None,
) -> dict[ProfileId, list[HazardEvent]]:
    """In-memory cell entry point for boundary tests and S3 simulation."""
    if frames.ndim != 3 or not len(frames) or len(frames) != len(timestamps):
        raise ValueError("expected nonempty luma frame/time arrays of equal length")
    if rgb is not None and rgb.shape != (*frames.shape, 3):
        raise ValueError("RGB array must match luma frame shape with three channels")
    pipeline = DetectionPipeline(
        (frames.shape[1], frames.shape[2]),
        profiles or [get_profile(profile) for profile in PROFILES],
    )
    for index, (frame, t) in enumerate(zip(frames, timestamps, strict=True)):
        pipeline.update(frame, None if rgb is None else rgb[index], float(t))
    step = float(timestamps[-1] - timestamps[-2]) if len(timestamps) > 1 else 1 / 25
    return pipeline.finish(end_s if end_s is not None else float(timestamps[-1]) + step)


def _cell_frames(
    path: Path, settings: Settings
) -> Generator[tuple[FloatArray, FloatArray, float], None, None]:
    with closing(iter_analysis(path, settings=settings)) as frames:
        for y, rgb, t in frames:
            linear = _RGB_LUT[rgb]
            cells = block_mean(linear)
            yield to_cells(y), cells, t


def analyze_detect_all(
    path: Path,
    *,
    settings: Settings | None = None,
    profiles: Sequence[ProfileParams] | None = None,
) -> dict[ProfileId, list[HazardEvent]]:
    """Detect all profiles in one pass; never publish a verified HazardTrack."""
    config = settings or Settings()
    media = probe(path, settings=config, require_bt709=True)
    pipeline = DetectionPipeline((90, 160), profiles or [get_profile(p) for p in PROFILES])
    last_t: float | None = None
    with closing(_cell_frames(path, config)) as frames:
        for luma, rgb, t in frames:
            pipeline.update(luma, rgb, t)
            last_t = t
    if last_t is None:
        raise DecodeError("decoder emitted no frames")
    return pipeline.finish(
        media.duration_s if media.duration_s > last_t else last_t + 1 / media.fps
    )


def analyze_detect(
    path: Path,
    profile: ProfileId | ProfileParams = "broadcast",
    *,
    settings: Settings | None = None,
) -> list[HazardEvent]:
    params = get_profile(profile) if isinstance(profile, str) else profile
    return analyze_detect_all(path, settings=settings, profiles=[params])[params.profile]
