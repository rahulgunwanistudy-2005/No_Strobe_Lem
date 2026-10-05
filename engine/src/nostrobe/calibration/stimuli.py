"""Slow, small-area calibration signals. Not publishable HazardTrack artifacts."""

import hashlib
import json
import subprocess
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import numpy as np

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import ByteArray, iter_analysis
from nostrobe.decode.process import StderrTail, stop
from nostrobe.errors import DecodeError

WIDTH, HEIGHT, FPS = 640, 360, 30
SYNC_TIMES = tuple(range(2, 23, 2))
PATCH = (32, 32, 64, 32)
BACKGROUND = (160, 32, 64, 32)
BLACK_REFERENCE = (16, 328, 16, 8)
WHITE_REFERENCE = (40, 328, 16, 8)
BIT_REGIONS = tuple((64 + bit * 24, 328, 16, 8) for bit in range(12))


def paint(frame: ByteArray, region: tuple[int, int, int, int], value: int) -> None:
    x, y, w, h = region
    frame[y : y + h, x : x + w] = value


def counter(frame: ByteArray, index: int) -> None:
    paint(frame, BLACK_REFERENCE, 16)
    paint(frame, WHITE_REFERENCE, 235)
    for bit, region in enumerate(BIT_REGIONS):
        paint(frame, region, 235 if index & (1 << bit) else 16)


def sync_frames() -> Iterator[ByteArray]:
    for index in range(24 * FPS):
        frame = np.full((HEIGHT, WIDTH, 3), 48, dtype=np.uint8)
        if index in {t * FPS for t in SYNC_TIMES}:
            paint(frame, PATCH, 235)
        counter(frame, index)
        yield frame


def composite_frames() -> Iterator[ByteArray]:
    codes = np.arange(16, 236, dtype=np.uint8)
    ramp = np.repeat(codes, 2)
    for index in range(30 * FPS):
        frame = np.full((HEIGHT, WIDTH, 3), 48, dtype=np.uint8)
        frame[32:280, 100:540] = ramp[None, :, None]
        counter(frame, index)
        yield frame


def encode(path: Path, frames: Iterator[ByteArray], config: Settings, font: Path) -> None:
    # Low-contrast large digits do not create a high-contrast flashing counter.
    command = [
        config.ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-color_range",
        "pc",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-i",
        "pipe:0",
        "-an",
        "-vf",
        f"drawtext=fontfile='{font}':text='Frame %{{n}}':x=110:y=285:fontsize=30:"
        "fontcolor=0x464646,scale=iw:ih:in_range=full:out_range=limited:"
        "out_color_matrix=bt709",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "0",
        "-pix_fmt",
        "yuv420p",
        "-x264-params",
        "colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off",
        "-threads",
        "1",
        "-filter_threads",
        "1",
        "-movflags",
        "+faststart",
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None and process.stderr is not None
    tail = StderrTail(process.stderr)
    try:
        for frame in frames:
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        if process.wait(timeout=60):
            raise DecodeError(f"calibration encoding failed: {tail.text()}")
    except (OSError, subprocess.SubprocessError) as exc:
        raise DecodeError(f"calibration encoding failed: {exc}: {tail.text()}") from exc
    finally:
        stop(process)


def generate(output: Path, font: Path, config: Settings) -> None:
    if not font.is_file():
        raise ValueError("a real font file is required for the burnt-in counter")
    output.mkdir(parents=True, exist_ok=True)
    (output / "README.md").write_text(
        "# Device calibration only\n\nSmall-area sync pulses and slow static ramps. "
        "Do not autoplay. These instant cue descriptors are not HazardTracks, "
        "have no verifier pass, and must never ship in release builds.\n"
    )
    for name, frames in [("sync", sync_frames()), ("compositing", composite_frames())]:
        path = output / f"{name}.mp4"
        encode(path, frames, config, font)
        cues = (
            [
                {"id": f"sync_{t}", "t_on": t, "t_off": t + 0.5, "alpha": 0.5, "gray": 0.5}
                for t in SYNC_TIMES
            ]
            if name == "sync"
            else [
                {
                    "id": f"composite_{i}",
                    "t_on": 3 * (i + 1),
                    "t_off": 3 * (i + 2),
                    "alpha": alpha,
                    "gray": gray,
                }
                for i, (alpha, gray) in enumerate(
                    (a, g) for a in (0.25, 0.5, 0.75) for g in (0.0, 0.25, 0.5)
                )
            ]
        )
        decoded_luma_codes: list[float] = []
        if name == "compositing":
            with closing(iter_analysis(path, settings=config)) as decoded:
                y, _, _ = next(decoded)
                decoded_luma_codes = (
                    np.median(y[80:220, 100:540], axis=0).reshape(-1, 2).mean(axis=1).tolist()
                )
        descriptor = {
            "format": "nostrobe-calibration",
            "version": 1,
            "production": False,
            "kind": name,
            "video": f"/calibration/{name}.mp4",
            "fps": FPS,
            "duration_s": 24 if name == "sync" else 30,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "cues": cues,
            "patch": PATCH,
            "background": BACKGROUND,
            "black_reference": BLACK_REFERENCE,
            "white_reference": WHITE_REFERENCE,
            "counter_bits": BIT_REGIONS,
            "patch_times_s": SYNC_TIMES if name == "sync" else [],
            "display_codes": list(range(16, 236)) if name == "compositing" else [],
            "decoded_luma_codes": decoded_luma_codes,
        }
        (output / f"{name}.json").write_text(json.dumps(descriptor, indent=2) + "\n")
