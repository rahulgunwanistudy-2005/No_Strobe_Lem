"""Source-hash-keyed memory-mapped samples, preserving pre-average code values."""

import json
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import ByteArray, block_mean, iter_analysis, probe
from nostrobe.detect.zigzag import IntArray
from nostrobe.domain.models import MediaInfo
from nostrobe.errors import DecodeError, NostrobeError
from nostrobe.luminance.color import bt709_to_linear
from nostrobe.luminance.curve import FloatArray, code10_to_cd_m2
from nostrobe.veil.composite import composite_luts

CACHE_VERSION = "s3-code-grid-640-v1"


@dataclass(frozen=True)
class FrameCache:
    media: MediaInfo
    directory: Path
    timestamps: FloatArray
    shards: tuple[tuple[str, int], ...]
    reductions: dict[tuple[float, float], tuple[int, int]] = field(default_factory=dict)

    groups: dict[tuple[float, float], tuple[IntArray, IntArray] | None] = field(
        default_factory=dict
    )

    def grouping(self, start: float, end: float) -> tuple[IntArray, IntArray] | None:
        key = (start, end)
        if key not in self.groups:
            labels = np.zeros(90 * 160, dtype=np.int64)
            for frame, _ in self.samples(start, end):
                blocks = np.ascontiguousarray(
                    frame.reshape(90, 4, 160, 4, 4).transpose(0, 2, 1, 3, 4)
                ).reshape(90 * 160, 64)
                unique, inverse = np.unique(blocks.view("V64").reshape(-1), return_inverse=True)
                pairs = labels * len(unique) + inverse
                _, labels = np.unique(pairs, return_inverse=True)
                if int(labels.max()) + 1 == 90 * 160:
                    self.groups[key] = None
                    break
            else:
                _, indices, mapping = np.unique(labels, return_index=True, return_inverse=True)
                self.groups[key] = (indices.astype(np.int64), mapping.reshape(90, 160))
        return self.groups[key]

    def grouped_cells(
        self, frame: ByteArray, indices: IntArray, alpha: float, gray: float
    ) -> tuple[FloatArray, FloatArray]:
        blocks = frame.reshape(90, 4, 160, 4, 4).transpose(0, 2, 1, 3, 4)
        samples = blocks.reshape(90 * 160, 4, 4, 4)[indices]
        y_codes, rgb_codes = composite_luts(alpha, gray)
        y = code10_to_cd_m2(y_codes * 255 * 4)[samples[..., 0]]
        rgb = bt709_to_linear(rgb_codes)[samples[..., 1:]]

        def average(values: FloatArray) -> FloatArray:
            rows = values[:, :, 0].copy()
            for x in range(1, 4):
                rows += values[:, :, x]
            total = rows[:, 0].copy()
            for y in range(1, 4):
                total += rows[:, y]
            return np.asarray(total[None] / 16, dtype=np.float64)

        return average(y), average(rgb)

    def shape(self, start: float, end: float) -> tuple[int, int]:
        key = (start, end)
        if key not in self.reductions:
            rows = columns = True
            for frame, _ in self.samples(start, end):
                if rows:
                    rows = bool(np.all(frame == frame[:1]))
                if columns:
                    columns = bool(np.all(frame == frame[:, :1]))
                if not rows and not columns:
                    break
            self.reductions[key] = (1 if rows else 90, 1 if columns else 160)
        return self.reductions[key]

    def samples(
        self, start: float = 0, end: float | None = None
    ) -> Iterator[tuple[ByteArray, float]]:
        limit = self.media.duration_s if end is None else end
        base = 0
        for name, count in self.shards:
            times = self.timestamps[base : base + count]
            base += count
            if times[-1] < start or times[0] >= limit:
                continue
            data = np.load(self.directory / name, mmap_mode="r", allow_pickle=False)
            for frame, t in zip(data, times, strict=True):
                if start <= t < limit:
                    yield frame, float(t)

    def luminance(self, frame: ByteArray, alpha: float = 0, gray: float = 0) -> FloatArray:
        y_codes, _ = composite_luts(alpha, gray)
        lut = code10_to_cd_m2(y_codes * 255 * 4)
        cells = (frame.shape[1] // 4, frame.shape[0] // 4)
        return block_mean(lut[frame[..., 0]], cells)

    def cells(
        self, frame: ByteArray, alpha: float = 0, gray: float = 0
    ) -> tuple[FloatArray, FloatArray]:
        # Evaluate transfer on each original sample BEFORE block averaging.
        y_codes, rgb_codes = composite_luts(alpha, gray)
        y_lut = code10_to_cd_m2(y_codes * 255 * 4)
        rgb_lut = bt709_to_linear(rgb_codes)
        cells = (frame.shape[1] // 4, frame.shape[0] // 4)
        return block_mean(y_lut[frame[..., 0]], cells), block_mean(rgb_lut[frame[..., 1:]], cells)


def load_cache(path: Path, settings: Settings | None = None) -> FrameCache:
    config = settings or Settings()
    media = probe(path, settings=config, require_bt709=True)
    root = config.cache_dir
    root.mkdir(parents=True, exist_ok=True)
    directory = root / f"{media.source_sha256}-{CACHE_VERSION}"
    if not directory.exists():
        temporary = Path(tempfile.mkdtemp(prefix="decode-", dir=root))
        try:
            times: list[float] = []
            shards: list[tuple[str, int]] = []
            batch: list[ByteArray] = []

            def flush() -> None:
                name = f"samples_{len(shards):05d}.npy"
                np.save(temporary / name, np.stack(batch), allow_pickle=False)
                shards.append((name, len(batch)))
                batch.clear()

            with closing(iter_analysis(path, settings=config)) as decoded:
                for y, rgb, t in decoded:
                    batch.append(np.concatenate((y[..., None], rgb), axis=-1))
                    times.append(t)
                    if len(batch) == 32:
                        flush()
            if batch:
                flush()
            if not times:
                raise DecodeError("decoder emitted no frames")
            if media.duration_s <= times[-1]:
                media = media.model_copy(update={"duration_s": times[-1] + 1 / media.fps})
            np.save(temporary / "timestamps.npy", np.array(times), allow_pickle=False)
            (temporary / "manifest.json").write_text(
                json.dumps(
                    {
                        "media": media.model_dump(mode="json"),
                        "shards": shards,
                    }
                )
            )
            try:
                temporary.rename(directory)
            except OSError:
                if not directory.is_dir():
                    raise
                shutil.rmtree(temporary)
        except (OSError, ValueError, RuntimeError, NostrobeError):
            shutil.rmtree(temporary, ignore_errors=True)
            raise
    manifest = json.loads((directory / "manifest.json").read_text())
    cached_media = MediaInfo.model_validate(manifest["media"])
    media = cached_media.model_copy(update={"content_id": media.content_id})
    timestamps = np.load(directory / "timestamps.npy", mmap_mode="r", allow_pickle=False)
    return FrameCache(
        media, directory, timestamps, tuple((str(n), int(c)) for n, c in manifest["shards"])
    )
