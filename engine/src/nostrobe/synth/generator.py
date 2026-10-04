"""Seeded hazardous test media. Never autoplay the generated clips."""

import json
import math
import subprocess
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import ByteArray
from nostrobe.decode.process import StderrTail, stop
from nostrobe.errors import DecodeError
from nostrobe.luminance.color import red_transition, rgb24_to_linear
from nostrobe.luminance.curve import cd_m2_to_code10, code10_to_cd_m2, thr

Primitive = Literal[
    "flat",
    "full_flash",
    "regional_rect",
    "regional_tiles",
    "red",
    "moving_bar",
    "camera_burst",
    "lightning",
    "police",
    "isolated",
    "checker",
]


@dataclass(frozen=True)
class ClipSpec:
    name: str
    primitive: Primitive
    fps: int = 25
    width: int = 640
    height: int = 360
    duration_s: float = 3.0
    seed: int = 7
    code8: int = 64
    rate: float = 3.5
    delta_cd_m2: float = 60.0
    dark_cd_m2: float = 100.0
    duty: float = 0.5
    area: float = 1.0
    n_flashes: int = 1
    rgb_a: tuple[int, int, int] = (255, 0, 0)
    rgb_b: tuple[int, int, int] = (0, 0, 255)

    def __post_init__(self) -> None:
        if not self.name or not all(c.isalnum() or c == "_" for c in self.name):
            raise ValueError("clip name must contain only letters, digits or underscores")
        if (
            self.fps <= 0
            or self.width <= 0
            or self.height <= 0
            or self.width % 2
            or self.height % 2
        ):
            raise ValueError("positive fps and even dimensions are required for yuv420p")
        if not math.isfinite(self.duration_s) or self.duration_s <= 0:
            raise ValueError("duration must be positive and finite")
        if not math.isfinite(self.rate) or not 0 < self.rate <= self.fps / 2:
            raise ValueError("flash rate must be positive and no greater than fps/2")
        if not 0 < self.duty < 1 or not 0 < self.area <= 1 or not 16 <= self.code8 <= 235:
            raise ValueError("invalid duty, area or limited-range code")
        if not 0 <= self.dark_cd_m2 < self.dark_cd_m2 + self.delta_cd_m2 <= 200:
            raise ValueError("luminance pair must lie within SDR 0..200 cd/m²")
        if self.n_flashes not in {1, 2, 3}:
            raise ValueError("isolated clips support one, two or three flashes")
        if any(not 0 <= value <= 255 for value in (*self.rgb_a, *self.rgb_b)):
            raise ValueError("rgb channels must lie within 0..255")

    @property
    def n_frames(self) -> int:
        return math.ceil(self.duration_s * self.fps)

    @property
    def is_rgb(self) -> bool:
        return self.primitive in {"red", "police"}


class TruthInterval(BaseModel):
    model_config = ConfigDict(frozen=True)
    t_start: float
    t_end: float


class ClipTruth(BaseModel):
    model_config = ConfigDict(frozen=True)
    format_version: Literal["1.0"] = "1.0"
    profile: Literal["broadcast"] = "broadcast"
    label: Literal["must_fail", "must_pass"]
    expected_intervals: list[TruthInterval]
    parameters: dict[str, object]
    peak_changes_per_s: int = Field(ge=0)
    measured_area_fraction: float = Field(ge=0, le=1)
    encoded_dark_cd_m2: float
    encoded_bright_cd_m2: float
    notes: str


def _codes(spec: ClipSpec) -> tuple[int, int]:
    codes = cd_m2_to_code10(np.array([spec.dark_cd_m2, spec.dark_cd_m2 + spec.delta_cd_m2]))
    quantized = np.rint(codes / 4).astype(np.uint8)
    return int(quantized[0]), int(quantized[1])


def _states(spec: ClipSpec) -> list[bool]:
    if spec.primitive in {"flat", "checker"}:
        return [False] * spec.n_frames
    states = []
    for frame in range(spec.n_frames):
        time = frame / spec.fps
        # Begin dark so every pulse has an analytic opposing transition pair.
        cycle = time * spec.rate
        active = cycle % 1 >= 1 - spec.duty
        if spec.primitive == "isolated":
            active = active and int(cycle) < spec.n_flashes
        elif spec.primitive == "camera_burst":
            active = active and 0.5 <= time < 2.5
        elif spec.primitive == "lightning":
            active = 0.6 <= time < 0.72 or 1.6 <= time < 1.72
        states.append(active)
    return states


def _mask(spec: ClipSpec) -> np.ndarray[tuple[int, ...], np.dtype[np.bool_]]:
    mask = np.zeros((spec.height, spec.width), dtype=np.bool_)
    count = round(spec.area * mask.size)
    if spec.primitive == "regional_tiles":
        # Randomize 2×2 blocks so the encoded YUV and analysis cells preserve area.
        tiles = np.zeros((spec.height // 2, spec.width // 2), dtype=np.bool_)
        rng = np.random.default_rng(spec.seed)
        tiles.flat[rng.permutation(tiles.size)[: round(spec.area * tiles.size)]] = True
        return np.repeat(np.repeat(tiles, 2, axis=0), 2, axis=1)
    mask.flat[:count] = True  # Rectangle plus a partial boundary row, exact pixel area.
    return mask


def iter_frames(spec: ClipSpec) -> Iterator[ByteArray]:
    """Pure numpy primitives; retains only one frame plus the temporal state list."""
    dark, bright = _codes(spec)
    mask = _mask(spec)
    checker = (np.indices((spec.height, spec.width)).sum(axis=0) // 8) % 2 == 0
    for index, active in enumerate(_states(spec)):
        if spec.is_rgb:
            color = spec.rgb_b if active else spec.rgb_a
            yield np.broadcast_to(
                np.array(color, dtype=np.uint8), (spec.height, spec.width, 3)
            ).copy()
            continue
        frame = np.full((spec.height, spec.width), dark, dtype=np.uint8)
        if spec.primitive == "flat":
            frame.fill(spec.code8)
        elif spec.primitive == "checker":
            frame[checker] = bright
        elif spec.primitive == "moving_bar":
            bar_width = max(1, round(spec.width * spec.area))
            left = index * 7 % spec.width
            columns = (np.arange(bar_width) + left) % spec.width
            frame[:, columns] = bright
        elif active:
            frame[mask] = bright
        yield frame


def analytic_truth(spec: ClipSpec) -> ClipTruth:
    """Independent sampled square-wave truth; no production detector is called.

    Spatial stress cases are isolated subthreshold pulses/moving areas in the
    smoke suite; they do not claim unsampled or post-codec detection accuracy.
    """
    dark, bright = _codes(spec)
    luminance = code10_to_cd_m2(np.array([dark * 4, bright * 4]))
    if spec.primitive == "flat":
        luminance = code10_to_cd_m2(np.array([spec.code8 * 4, spec.code8 * 4]))
    elif spec.is_rgb:
        codes = np.rint(
            16
            + 219 * (np.array([spec.rgb_a, spec.rgb_b]) / 255) @ np.array([0.2126, 0.7152, 0.0722])
        )
        luminance = np.sort(code10_to_cd_m2(codes * 4))
    states = _states(spec)
    changes = np.array(
        [index / spec.fps for index in range(1, len(states)) if states[index] != states[index - 1]]
    )
    change_indices = np.rint(changes * spec.fps).astype(np.int64)
    counts = [
        int(np.count_nonzero((change_indices > index - spec.fps) & (change_indices <= index)))
        for index in change_indices
    ]
    area = float(_mask(spec).mean())
    qualifies = bool(luminance[1] - luminance[0] >= thr(luminance[:1])[0])
    if spec.is_rgb:
        pair = rgb24_to_linear(np.array([spec.rgb_a, spec.rgb_b], dtype=np.uint8))
        qualifies = bool(red_transition(pair[0], pair[1]))
    leading = [
        index / spec.fps
        for index in range(1, len(states))
        if states[index] and not states[index - 1]
    ]
    dense = len(leading) > 1 and any(
        b - a < 0.36 for a, b in zip(leading, leading[1:], strict=False)
    )
    failing = [
        t
        for t, count in zip(changes, counts, strict=True)
        if count > 6 and area > 0.25 and qualifies and dense
    ]
    if spec.primitive in {"flat", "checker", "moving_bar"}:
        failing = []
        if spec.primitive == "moving_bar" and (
            spec.area > 0.25 or spec.width / (7 * spec.fps) < 0.36
        ):
            raise ValueError("moving-bar truth requires area <=25% and leading spacing >=0.36s")
    # Evaluate every sampled frame so separated bursts produce separate intervals.
    counts_by_frame = [
        int(np.count_nonzero((change_indices > index - spec.fps) & (change_indices <= index)))
        for index in range(spec.n_frames)
    ]
    hot = [count > 6 and bool(failing) for count in counts_by_frame]
    intervals: list[TruthInterval] = []
    start: int | None = None
    for index, active in enumerate([*hot, False]):
        if active and start is None:
            start = index
        elif not active and start is not None:
            intervals.append(TruthInterval(t_start=start / spec.fps, t_end=index / spec.fps))
            start = None
    if spec.primitive == "moving_bar":
        # A single moving bar traverses a cell at most once per accepted leading period.
        counts = [2 if spec.n_frames > 1 else 0]
    return ClipTruth(
        label="must_fail" if failing else "must_pass",
        expected_intervals=intervals,
        parameters=asdict(spec),
        peak_changes_per_s=max(counts, default=0) if qualifies else 0,
        measured_area_fraction=area,
        encoded_dark_cd_m2=float(luminance[0]),
        encoded_bright_cd_m2=float(luminance[1]),
        notes=(
            "Broadcast product interpretation on sampled raw states; "
            "codec errors measured separately."
        ),
    )


def encode(path: Path, spec: ClipSpec, *, settings: Settings | None = None) -> None:
    """Stream H.264 CRF 10, limited-range yuv420p and explicit BT.709 tags."""
    config = settings or Settings()
    if not path.name.startswith("HAZARD_") or path.suffix != ".mp4":
        raise ValueError("synthetic paths require HAZARD_ prefix and .mp4 extension")
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "README.md").write_text(
        "# WARNING: hazardous synthetic test media\n\n"
        "These clips can contain flashing harmful to photosensitive viewers. "
        "Do not autoplay or review raw clips. Use truth sidecars and numerical traces.\n"
    )
    pixel_format = "rgb24" if spec.is_rgb else "yuv420p"
    command = [
        config.ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        pixel_format,
        "-s",
        f"{spec.width}x{spec.height}",
        "-r",
        str(spec.fps),
        "-color_range",
        "pc" if spec.is_rgb else "tv",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "10",
        "-x264-params",
        "colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off:psy=0:aq-mode=0:qpmax=6",
        "-pix_fmt",
        "yuv420p",
        "-color_range",
        "tv",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-threads",
        "1",
    ]
    if spec.is_rgb:
        command += [
            "-vf",
            "scale=iw:ih:flags=area:in_range=full:out_range=limited:out_color_matrix=bt709",
        ]
    command += ["-movflags", "+faststart", str(path)]
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise DecodeError(f"could not start encoder: {exc}") from exc
    assert process.stdin is not None and process.stderr is not None
    tail = StderrTail(process.stderr)
    broken_pipe = False
    try:
        neutral = bytes([128]) * (spec.width * spec.height // 2)
        try:
            for frame in iter_frames(spec):
                process.stdin.write(frame.tobytes())
                if not spec.is_rgb:
                    process.stdin.write(neutral)
            process.stdin.close()
        except BrokenPipeError:
            broken_pipe = True
        result = process.wait(timeout=60)
        if result != 0 or broken_pipe:
            raise DecodeError(f"ffmpeg encode failed ({result}): {tail.text()}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DecodeError(f"encode failed: {exc}; {tail.text()}") from exc
    finally:
        stop(process)
        tail.thread.join(timeout=5)


def write_clip(directory: Path, spec: ClipSpec, *, settings: Settings | None = None) -> Path:
    truth = analytic_truth(spec)
    path = directory / f"HAZARD_{spec.name}.mp4"
    encode(path, spec, settings=settings)
    path.with_suffix(".truth.json").write_text(truth.model_dump_json(indent=2) + "\n")
    return path


def smoke_specs(seed: int = 7) -> list[ClipSpec]:
    return [
        ClipSpec("flat", "flat", seed=seed, duration_s=1),
        ClipSpec("rate_3", "full_flash", seed=seed, rate=3),
        ClipSpec("rate_3_5", "full_flash", seed=seed, rate=3.5),
        ClipSpec("area_24", "regional_rect", seed=seed, area=0.24),
        ClipSpec("area_26", "regional_rect", seed=seed, area=0.26),
        ClipSpec("tiles_26", "regional_tiles", seed=seed, area=0.26),
        ClipSpec("delta_19", "full_flash", seed=seed, delta_cd_m2=19),
        ClipSpec("delta_21", "full_flash", seed=seed, delta_cd_m2=21),
        ClipSpec("red_blue", "red", seed=seed),
        ClipSpec("moving_bar", "moving_bar", seed=seed, area=0.10),
        ClipSpec("camera_burst", "camera_burst", seed=seed, rate=5),
        ClipSpec("lightning", "lightning", seed=seed),
        ClipSpec("police", "police", seed=seed),
        *[
            ClipSpec(f"isolated_{count}", "isolated", seed=seed, n_flashes=count)
            for count in (1, 2, 3)
        ],
    ]


def generate_suite(
    directory: Path, suite: str = "smoke", seed: int = 7, *, settings: Settings | None = None
) -> list[Path]:
    if suite != "smoke":
        raise ValueError("only the smoke suite is implemented in S1")
    specs = smoke_specs(seed)
    paths = [write_clip(directory, spec, settings=settings) for spec in specs]
    manifest = {"suite": suite, "seed": seed, "clips": [asdict(spec) for spec in specs]}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return paths
