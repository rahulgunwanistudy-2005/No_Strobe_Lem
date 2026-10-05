"""Read capture timestamps and small regions without playing recorded content."""

import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from nostrobe.calibration.stimuli import (
    BACKGROUND,
    BIT_REGIONS,
    BLACK_REFERENCE,
    PATCH,
    WHITE_REFERENCE,
)
from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import ByteArray
from nostrobe.decode.process import StderrTail, stop
from nostrobe.errors import DecodeError


@dataclass(frozen=True)
class FrameSignals:
    counter: int
    patch: float
    background: float
    ramp: np.ndarray[Any, np.dtype[np.float64]]


@dataclass(frozen=True)
class Capture:
    times: list[float]
    frames: list[FrameSignals]
    source_sha256: str
    effective_fps: float


def read_capture(path: Path, crop: str | None, config: Settings) -> Capture:
    command = [
        config.ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_frames",
        "-show_entries",
        "frame=best_effort_timestamp_time",
        "-of",
        "json",
        str(path),
    ]
    try:
        output = subprocess.run(command, capture_output=True, check=True, timeout=60)
        times = [
            float(frame["best_effort_timestamp_time"])
            for frame in json.loads(output.stdout)["frames"]
        ]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        raise DecodeError(f"cannot probe recording timestamps: {exc}") from exc
    if len(times) < 2 or not all(math.isfinite(t) for t in times):
        raise ValueError("recording needs finite frame timestamps")
    deltas = np.diff(times)
    if np.any(deltas <= 0):
        raise ValueError("recording timestamps must increase")
    fps = float(1 / np.median(deltas))
    if fps < 59.9 or (len(times) - 1) / (times[-1] - times[0]) < 59.9:
        raise ValueError("recording must be captured at at least 60 fps (59.94 accepted)")
    filters = ([f"crop={crop}"] if crop else []) + ["scale=640:360:flags=area,format=rgb24"]
    command = [
        config.ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(path),
        "-an",
        "-vf",
        ",".join(filters),
        "-fps_mode",
        "passthrough",
        "-threads",
        "1",
        "-filter_threads",
        "1",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None and process.stderr is not None
    tail = StderrTail(process.stderr)
    frames = []
    # Keep only per-frame regions/counters; never retain the full recording in RAM.
    if len(times) > 36000:
        stop(process)
        raise ValueError("split recordings longer than ten minutes")
    try:
        for _ in times:
            data = process.stdout.read(640 * 360 * 3)
            if len(data) != 640 * 360 * 3:
                raise DecodeError("recording decode/frame timestamp count mismatch")
            frame = np.frombuffer(data, dtype=np.uint8).reshape(360, 640, 3)
            frames.append(measure_frame(frame))
        if process.stdout.read(1) or process.wait(timeout=30):
            raise DecodeError(f"recording decode failed: {tail.text()}")
    finally:
        stop(process)
    return Capture(times, frames, file_hash(path), fps)


def region_value(frame: ByteArray, box: list[int] | tuple[int, ...]) -> float:
    x, y, w, h = box
    return float(np.median(frame[y : y + h, x : x + w]))


def frame_counter(frame: ByteArray) -> int:
    low = region_value(frame, BLACK_REFERENCE)
    high = region_value(frame, WHITE_REFERENCE)
    if high - low < 20:
        raise ValueError("counter references missing or obscured; check the video crop")
    return sum(
        (1 << bit)
        for bit, box in enumerate(BIT_REGIONS)
        if region_value(frame, box) > (low + high) / 2
    )


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def measure_frame(frame: ByteArray) -> FrameSignals:
    row = np.median(frame[80:220, 100:540].astype(np.float64), axis=(0, 2))
    return FrameSignals(
        frame_counter(frame),
        region_value(frame, PATCH),
        region_value(frame, BACKGROUND),
        row.reshape(-1, 2).mean(axis=1),
    )


def sync_measurement(capture: Capture, descriptor: dict[str, Any], scenario: str) -> dict[str, Any]:
    if descriptor.get("kind") != "sync" or descriptor.get("production") is not False:
        raise ValueError("a sync calibration descriptor is required")
    if scenario not in {"steady", "seek", "pause_resume"}:
        raise ValueError("scenario must identify steady, seek or pause_resume")
    patch = np.array([f.patch - f.background for f in capture.frames])
    baseline = np.array([f.background for f in capture.frames])
    patch_edges = np.flatnonzero((patch[1:] > 40) & (patch[:-1] <= 40)) + 1
    veil_edges = np.flatnonzero(np.diff(baseline) > 15) + 1
    samples = []
    matched: set[int] = set()
    fps = float(descriptor["fps"])
    expected = set(round(t * fps) for t in descriptor["patch_times_s"])
    for index in patch_edges:
        media_frame = capture.frames[int(index)].counter
        if media_frame not in expected:
            raise ValueError("observed patch does not match the source frame counter")
        candidates = [
            int(v)
            for v in veil_edges
            if int(v) not in matched
            and abs(capture.times[int(v)] - capture.times[int(index)]) <= 0.5
        ]
        if not candidates:
            raise ValueError("patch has no matching veil onset within 500 ms")
        edge = min(candidates, key=lambda v: abs(capture.times[v] - capture.times[int(index)]))
        matched.add(edge)
        samples.append(
            {
                "media_frame": media_frame,
                "patch_capture_s": capture.times[int(index)],
                "veil_capture_s": capture.times[edge],
                "offset_s": capture.times[edge] - capture.times[int(index)],
            }
        )
    if len(samples) < 5:
        raise ValueError("at least five measured patch/veil pairs are required per scenario")
    values = np.array([sample["offset_s"] for sample in samples])
    absolute = np.abs(values)
    return {
        "status": "measured",
        "scenario": scenario,
        "capture_sha256": capture.source_sha256,
        "stimulus_sha256": descriptor["source_sha256"],
        "capture_fps": capture.effective_fps,
        "samples": samples,
        "median_s": float(np.median(values)),
        "p95_abs_s": float(np.percentile(absolute, 95)),
        "max_abs_s": float(absolute.max()),
        "quantization_bound_s": float(max(np.diff(capture.times))),
    }


def combine_sync(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if {run["scenario"] for run in runs} != {"steady", "seek", "pause_resume"}:
        raise ValueError("all three playback scenarios are required")
    if any(run["status"] != "measured" for run in runs):
        raise ValueError("every recording must have measured samples")
    values = np.array([s["offset_s"] for run in runs for s in run["samples"]])
    p95 = float(np.percentile(np.abs(values), 95))
    tolerance = max(p95 * 1.5, 0.1)
    # Do not silently use the requested p95 formula if observed outliers exceed
    # it. The verifier needs a bound for every observed delay.
    observed_max = float(np.max(np.abs(values)))
    if observed_max > tolerance:
        raise ValueError("observed max exceeds p95-derived tolerance; investigate outliers")
    return {
        "status": "measured",
        "format_version": 1,
        "runs": runs,
        "median_s": float(np.median(values)),
        "p95_abs_s": p95,
        "max_abs_s": observed_max,
        "sync_tolerance_s": tolerance,
        "formula": "max(p95 absolute offset * 1.5, 0.1)",
    }


def compositing_measurement(capture: Capture, descriptor: dict[str, Any]) -> dict[str, Any]:
    if descriptor.get("kind") != "compositing" or descriptor.get("production") is not False:
        raise ValueError("a compositing calibration descriptor is required")
    source_codes = np.array(descriptor["display_codes"], dtype=np.float64)
    samples: dict[str, list[np.ndarray[Any, np.dtype[np.float64]]]] = {}
    for frame in capture.frames:
        t = frame.counter / descriptor["fps"]
        # Exclude every boundary by half a second, including decoder seek frames.
        for cue in [
            {"id": "baseline", "t_on": 0, "t_off": 3, "alpha": 0, "gray": 0},
            *descriptor["cues"],
        ]:
            if cue["t_on"] + 0.5 < t < cue["t_off"] - 0.5:
                samples.setdefault(cue["id"], []).append(frame.ramp)
    luma_codes = np.asarray(descriptor.get("decoded_luma_codes", []), dtype=np.float64)
    if luma_codes.shape != source_codes.shape:
        raise ValueError("descriptor must contain actual decoded source luma codes")
    cases = []
    baseline = samples.get("baseline", [])
    if len(baseline) < 10:
        raise ValueError("need ten unobscured baseline frames")
    observed_source = np.median(baseline, axis=0)
    if float(np.max(np.abs(observed_source - source_codes))) > 2:
        raise ValueError("capture/source baseline differs by >2 codes; check range/color/crop")
    for cue in descriptor["cues"]:
        if len(samples.get(cue["id"], [])) < 10:
            raise ValueError(f"missing stable capture samples for {cue['id']}")
        measured = np.median(samples[cue["id"]], axis=0)
        predicted = (1 - cue["alpha"]) * observed_source + cue["alpha"] * cue["gray"] * 255
        fit = np.polyfit(observed_source, measured, 1)
        # Gray pixels captured in full-range RGB map back to limited BT.709 Y.
        # Compare this separately to the engine's original decoded code-space model.
        captured_y = 16 + measured * 219 / 255
        predicted_y = (1 - cue["alpha"]) * luma_codes + cue["alpha"] * cue["gray"] * 255
        y_fit = np.polyfit(luma_codes, captured_y, 1)
        cases.append(
            {
                "alpha": cue["alpha"],
                "gray": cue["gray"],
                "sample_frames": len(samples[cue["id"]]),
                "source_codes": observed_source.tolist(),
                "measured_codes": measured.tolist(),
                "max_error_codes": float(np.max(np.abs(measured - predicted))),
                "mean_error_codes": float(np.mean(np.abs(measured - predicted))),
                "fit_slope": float(fit[0]),
                "fit_intercept": float(fit[1]),
                "engine_y_max_error_codes": float(np.max(np.abs(captured_y - predicted_y))),
                "engine_y_fit_slope": float(y_fit[0]),
                "engine_y_fit_intercept": float(y_fit[1]),
            }
        )
    if len(cases) != 9:
        raise ValueError("all nine alpha/gray combinations are required")
    maximum = max(case["max_error_codes"] for case in cases)
    y_maximum = max(case["engine_y_max_error_codes"] for case in cases)
    return {
        "status": "measured",
        "format_version": 1,
        "capture_sha256": capture.source_sha256,
        "stimulus_sha256": descriptor["source_sha256"],
        "capture_fps": capture.effective_fps,
        "domain": "captured full-range RGB display code; baseline checked before overlay fit",
        "model": "(1-alpha)*source_code + alpha*gray*255",
        "cases": cases,
        "max_error_codes": maximum,
        "engine_y_max_error_codes": y_maximum,
        "model_passes_two_code_gate": maximum <= 2 and y_maximum <= 2,
    }
