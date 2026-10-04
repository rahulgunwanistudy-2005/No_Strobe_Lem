"""Static trace-only reports; raw source frames are never embedded or played."""

import base64
from collections.abc import Sequence
from importlib.resources import files
from io import BytesIO

import numpy as np
from jinja2 import Environment, select_autoescape
from matplotlib.figure import Figure

from nostrobe.decode.cache import FrameCache
from nostrobe.detect.luma_flash import LumaFlashDetector
from nostrobe.detect.red_flash import RedFlashDetector
from nostrobe.domain.models import HazardTrack
from nostrobe.domain.profiles import get_profile
from nostrobe.veil.composite import veil_timeline

DISCLAIMER = (
    "No Strobe-lem is a viewing aid that reduces flashing according to published broadcast "
    "guidelines. It is not a medical device and cannot guarantee that content is safe for every "
    "person with photosensitive epilepsy."
)


def _image(figure: Figure) -> str:
    output = BytesIO()
    figure.savefig(output, format="png", backend="agg")
    return base64.b64encode(output.getvalue()).decode("ascii")


def _timeline(track: HazardTrack) -> str:
    figure = Figure(figsize=(9, 2), layout="constrained")
    axis = figure.subplots()
    times = np.linspace(0, track.media.duration_s, 1000)
    alpha = [veil_timeline(track.veils, float(t))[0] for t in times]
    axis.plot(times, alpha, color="#446688")
    axis.set(xlabel="Media time (s)", ylabel="Veil opacity", ylim=(-0.02, 1.02))
    return _image(figure)


def _traces(track: HazardTrack, cache: FrameCache) -> list[dict[str, str]]:
    charts: list[dict[str, str]] = []
    for event in track.events:
        times: list[float] = []
        before: list[float] = []
        after: list[float] = []
        start = max(0, event.t_start - 1.5)
        end = min(cache.media.duration_s, event.t_end + 1)
        params = get_profile(track.profile)
        luma_detector = LumaFlashDetector((90, 160), params.leading_edge_spacing_s)
        red_detector = RedFlashDetector((90, 160), params.leading_edge_spacing_s)
        peaks = np.zeros((90, 160), dtype=np.int64)
        for frame, t in cache.samples(start, end):
            luma, rgb = cache.cells(frame)
            counts, raw = luma_detector.update(luma, t)
            red_counts, red_raw = red_detector.update(rgb, t)
            if event.t_start <= t < event.t_end:
                measured = red_counts if event.kind == "red_flash" else counts
                if event.kind == "extended_flashing":
                    measured = np.maximum(raw, red_raw)
                peaks = np.maximum(peaks, measured)
        group = peaks == peaks.max()
        for frame, t in cache.samples(start, end):
            alpha, gray = veil_timeline(track.veils, t)
            original = cache.luminance(frame)
            veiled = cache.luminance(frame, alpha, gray)
            times.append(t)
            before.append(float(original[group].mean()))
            after.append(float(veiled[group].mean()))
        figure = Figure(figsize=(9, 2.5), layout="constrained")
        axis = figure.subplots()
        axis.plot(times, before, label="Before", color="#ad6940")
        axis.plot(times, after, label="After veil", color="#346a8a")
        axis.set(xlabel="Media time (s)", ylabel="Luminance (cd/m²)")
        axis.legend()
        charts.append({"id": event.id, "image": _image(figure)})
    return charts


def render(tracks: HazardTrack | Sequence[HazardTrack], *, cache: FrameCache | None = None) -> str:
    values = [tracks] if isinstance(tracks, HazardTrack) else list(tracks)
    if not values:
        raise ValueError("report requires at least one track")
    template = files("nostrobe.report").joinpath("templates/report.html.j2").read_text()
    environment = Environment(autoescape=select_autoescape(default=True))
    return environment.from_string(template).render(
        media=values[0].media,
        disclaimer=DISCLAIMER,
        profiles=[
            {
                "track": track,
                "timeline": _timeline(track),
                "traces": _traces(track, cache) if cache is not None else [],
            }
            for track in values
        ],
    )
