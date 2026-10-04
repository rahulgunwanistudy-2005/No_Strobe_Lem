"""Deterministic display-code effects over licensed footage; never autoplay."""

import subprocess
from pathlib import Path

import numpy as np

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import ByteArray
from nostrobe.errors import DecodeError


def effect_states(effect: str, fps: int, duration_s: float = 3) -> list[bool]:
    times = np.arange(round(duration_s * fps)) / fps
    if effect == "camera_burst":
        states = (times * 5 % 1 >= 0.65) & (times >= 0.4) & (times < 2.6)
    elif effect == "lightning":
        states = (times * 4 % 1 >= 0.7) & (times >= 0.2) & (times < 2.8)
    elif effect == "police":
        states = times * 4 % 1 >= 0.5
    elif effect == "strobe":
        states = times * 5 % 1 >= 0.5
    elif effect == "glitch":
        states = times * 8 % 1 >= 0.7
    else:
        raise ValueError(f"unknown composite effect: {effect}")
    return [bool(v) for v in states]


def composite_frames(
    path: Path, effect: str, start_s: float, fps: int, *, settings: Settings | None = None
) -> list[ByteArray]:
    config = settings or Settings()
    command = [
        config.ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-ss",
        str(start_s),
        "-i",
        str(path),
        "-t",
        "3",
        "-an",
        "-vf",
        f"fps={fps},scale=640:360:flags=area:out_color_matrix=bt709,format=rgb24",
        "-threads",
        "1",
        "-filter_threads",
        "1",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    try:
        result = subprocess.run(command, capture_output=True, check=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise DecodeError(f"reference-footage decode failed: {exc}") from exc
    size = 640 * 360 * 3
    states = effect_states(effect, fps)
    if len(result.stdout) != size * len(states):
        raise DecodeError("reference excerpt did not contain the expected frames")
    source = np.frombuffer(result.stdout, dtype=np.uint8).reshape(-1, 360, 640, 3)
    output = []
    for frame, active in zip(source, states, strict=True):
        if effect == "police":
            overlay = np.array((0, 0, 255) if active else (255, 0, 0))
        else:
            overlay = np.full(3, 255 if active else 0)
        output.append(np.rint(0.1 * frame + 0.9 * overlay).astype(np.uint8))
    return output


def encode_rgb(path: Path, frames: list[ByteArray], fps: int, settings: Settings) -> None:
    if not path.name.startswith("HAZARD_"):
        raise ValueError("composite output requires HAZARD_ prefix")
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "README.md").write_text(
        "# WARNING: hazardous evaluation composites\n\n"
        "Do not autoplay or review raw clips. Review truth, traces and metrics only.\n"
    )
    command = [
        settings.ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        "640x360",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-an",
        "-vf",
        "scale=iw:ih:flags=area:in_range=full:out_range=limited:out_color_matrix=bt709",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "10",
        "-x264-params",
        "psy=0:aq-mode=0:qpmax=6",
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
        str(path),
    ]
    try:
        subprocess.run(
            command,
            input=b"".join(frame.tobytes() for frame in frames),
            capture_output=True,
            check=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DecodeError(f"composite encode failed: {exc}") from exc


def composite_real(path: Path, output: Path, seed: int) -> None:
    # Seed selects a reproducible excerpt; effect-specific evaluation calls use
    # the explicit scenario timestamps committed in the manifest.
    config = Settings()
    encode_rgb(output, composite_frames(path, "strobe", seed % 30, 25), 25, config)
