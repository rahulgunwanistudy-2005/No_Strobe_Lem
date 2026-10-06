"""ffmpeg/ffprobe streaming decode with real presentation timestamps."""

import hashlib
import json
import re
import subprocess
from collections import deque
from collections.abc import Generator
from fractions import Fraction
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import ValidationError

from nostrobe.config import Settings
from nostrobe.decode.process import stop
from nostrobe.domain.models import MediaInfo
from nostrobe.errors import DecodeError, UnsupportedMediaError
from nostrobe.luminance.curve import FloatArray, code10_to_cd_m2

ByteArray = NDArray[np.uint8]
_PTS = re.compile(rb"\bn:\s*\d+.*?\bpts:\s*(-?\d+)\s")
_TIME_BASE = re.compile(rb"config in time_base:\s*(\d+/\d+)")
_LUMA_LUT = code10_to_cd_m2(np.arange(256, dtype=np.float64) * 4)


def probe(
    path: Path, *, settings: Settings | None = None, require_bt709: bool = False
) -> MediaInfo:
    config = settings or Settings()
    try:
        result = subprocess.run(
            [
                config.ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        transfer = stream.get("color_transfer", "unknown")
        if transfer not in {"bt709", "smpte170m", "bt470m", "bt470bg", "gamma22", "gamma28"}:
            raise UnsupportedMediaError(f"unsupported or unspecified transfer: {transfer}")
        if stream.get("color_range") != "tv":
            raise UnsupportedMediaError("only explicitly tagged limited-range SDR is supported")
        if stream.get("pix_fmt") not in {"yuv420p", "yuv422p", "yuv444p"}:
            raise UnsupportedMediaError("S1 decoder requires 8-bit planar YUV SDR")
        if require_bt709 and any(
            stream.get(tag) != "bt709"
            for tag in ("color_transfer", "color_primaries", "color_space")
        ):
            raise UnsupportedMediaError("red analysis requires explicitly tagged BT.709 color")
        fps = float(Fraction(stream.get("avg_frame_rate") or stream["r_frame_rate"]))
        duration = float(stream.get("duration") or data["format"]["duration"])
        digest = hashlib.sha256()
        with path.open("rb") as source:
            while block := source.read(1024 * 1024):
                digest.update(block)
        return MediaInfo(
            content_id=path.stem,
            duration_s=duration,
            fps=fps,
            width=stream["width"],
            height=stream["height"],
            transfer="sdr",
            source_sha256=digest.hexdigest(),
        )
    except subprocess.CalledProcessError as exc:
        raise DecodeError(exc.stderr.decode(errors="replace")[-4000:]) from exc
    except (
        OSError,
        subprocess.TimeoutExpired,
        ValueError,
        KeyError,
        IndexError,
        ValidationError,
    ) as exc:
        raise DecodeError(f"could not probe {path.name}: {exc}") from exc


def _frames(
    path: Path, grid: tuple[int, int], mode: Literal["luma", "rgb", "analysis"], config: Settings
) -> Generator[tuple[ByteArray, float], None, None]:
    probe(path, settings=config, require_bt709=mode == "analysis")
    width, height = grid
    if width <= 0 or height <= 0:
        raise ValueError("grid dimensions must be positive")
    shape: tuple[int, ...]
    if mode == "luma":
        # Extract Y before conversion, then preserve numerical limited-range codes.
        filters = f"extractplanes=y,scale={width}:{height}:flags=area:in_range=full:out_range=full"
        pixel_format, shape = "gray", (height, width)
    elif mode == "rgb":
        filters = (
            f"scale={width}:{height}:flags=area:in_color_matrix=bt709:"
            "out_color_matrix=bt709:in_range=limited:out_range=full,format=rgb24"
        )
        pixel_format, shape = "rgb24", (height, width, 3)
    else:
        # One input decoder feeds both branches; the left RGB triplet stores
        # unexpanded numerical Y codes, the right triplet carries actual RGB.
        filters = (
            "split=2[y][rgb];[y]extractplanes=y,"
            f"scale={width}:{height}:flags=area:in_range=full:out_range=full,"
            "format=rgb24[yc];[rgb]"
            f"scale={width}:{height}:flags=area:in_color_matrix=bt709:"
            "out_color_matrix=bt709:in_range=limited:out_range=full,"
            "format=rgb24[rc];[yc][rc]hstack=inputs=2"
        )
        pixel_format, shape = "rgb24", (height, width * 2, 3)
    filters += ",setpts=PTS-STARTPTS,showinfo"
    command = [
        config.ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "info",
        "-noautorotate",
        "-threads",
        "1",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-an",
        "-sn",
        "-dn",
        "-vf",
        filters,
        "-filter_threads",
        "1",
        "-fps_mode",
        "passthrough",
        "-pix_fmt",
        pixel_format,
        "-threads",
        "1",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise DecodeError(f"could not start decoder: {exc}") from exc
    assert process.stdout is not None and process.stderr is not None
    timestamps: Queue[float | DecodeError] = Queue(maxsize=16)
    cancel = Event()
    errors: deque[bytes] = deque(maxlen=40)

    def drain() -> None:
        assert process.stderr is not None
        time_base: Fraction | None = None
        while line := process.stderr.readline(4096):
            errors.append(line)
            base = _TIME_BASE.search(line)
            if base:
                time_base = Fraction(base.group(1).decode())
            match = _PTS.search(line)
            if match:
                # showinfo pts_time is rounded differently across ffmpeg releases.
                # Integer PTS and filter time base retain exact presentation timing.
                pts: float | DecodeError = (
                    float(int(match.group(1)) * time_base)
                    if time_base is not None
                    else DecodeError("decoder did not report the filter time base")
                )
                while not cancel.is_set():
                    try:
                        timestamps.put(pts, timeout=0.1)
                        break
                    except Full:
                        continue

    thread = Thread(target=drain, daemon=True)
    thread.start()
    size = int(np.prod(shape))
    try:
        while True:
            chunks = bytearray()
            while len(chunks) < size:
                chunk = process.stdout.read(size - len(chunks))
                if not chunk:
                    break
                chunks.extend(chunk)
            if not chunks:
                break
            if len(chunks) != size:
                raise DecodeError("decoder emitted a truncated frame")
            try:
                pts = timestamps.get(timeout=5)
            except Empty as exc:
                raise DecodeError("decoder did not emit a presentation timestamp") from exc
            if isinstance(pts, DecodeError):
                raise pts
            yield np.frombuffer(chunks, dtype=np.uint8).reshape(shape).copy(), pts
        result = process.wait(timeout=30)
        thread.join(timeout=5)
        if result != 0:
            tail = b"".join(errors).decode(errors="replace")[-4000:]
            raise DecodeError(f"ffmpeg exited {result}: {tail}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DecodeError(f"decode failed: {exc}") from exc
    finally:
        cancel.set()
        if process.poll() is None:
            process.kill()
        thread.join(timeout=5)
        stop(process)


def iter_luma(
    path: Path, grid: tuple[int, int] = (640, 360), *, settings: Settings | None = None
) -> Generator[tuple[ByteArray, float], None, None]:
    """Limited-range Y' frames; close the iterator/contextlib.closing on early exit."""
    yield from _frames(path, grid, "luma", settings or Settings())


def iter_rgb(
    path: Path, grid: tuple[int, int] = (640, 360), *, settings: Settings | None = None
) -> Generator[tuple[ByteArray, float], None, None]:
    """Full-range BT.709 rgb24 frames and media-timeline PTS."""
    yield from _frames(path, grid, "rgb", settings or Settings())


def iter_analysis(
    path: Path, grid: tuple[int, int] = (640, 360), *, settings: Settings | None = None
) -> Generator[tuple[ByteArray, ByteArray, float], None, None]:
    """Synchronized Y/RGB from one bounded ffmpeg decoding pass."""
    for frame, t in _frames(path, grid, "analysis", settings or Settings()):
        yield frame[:, : grid[0], 0], frame[:, grid[0] :, :], t


def to_cells(luma_frame: ByteArray, cells: tuple[int, int] = (160, 90)) -> FloatArray:
    """Linearize first, then average blocks; accepts raised decode resolutions."""
    width, height = cells
    if luma_frame.ndim != 2 or luma_frame.dtype != np.uint8:
        raise ValueError("expected a 2D uint8 luma plane")
    rows, cols = luma_frame.shape
    if width <= 0 or height <= 0 or rows % height or cols % width:
        raise ValueError("decode dimensions must be multiples of cell dimensions")
    return block_mean(_LUMA_LUT[luma_frame], cells)


def block_mean(linear: FloatArray, cells: tuple[int, int] = (160, 90)) -> FloatArray:
    """Linear-light reduction with contiguous row sums, no per-cell loops."""
    width, height = cells
    rows, cols = linear.shape[:2]
    if min(cells) <= 0 or rows % height or cols % width:
        raise ValueError("decode dimensions must be multiples of cell dimensions")
    sx, sy = cols // width, rows // height
    horizontal = linear[:, ::sx].copy()
    for offset in range(1, sx):
        horizontal += linear[:, offset::sx]
    result = horizontal[::sy].copy()
    for offset in range(1, sy):
        result += horizontal[offset::sy]
    result /= sx * sy
    return result
