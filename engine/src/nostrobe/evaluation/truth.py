"""Offline oracle: enumerate raw state reversals, paired flashes and windows.

No production detector, counter, area helper or event builder is imported.
Threshold values express the documented product interpretations, not certification.
"""

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

from nostrobe.decode.ffmpeg import ByteArray
from nostrobe.luminance.curve import FloatArray, code10_to_cd_m2
from nostrobe.synth.generator import TruthInterval


class ProfileTruth(BaseModel):
    model_config = ConfigDict(frozen=True)
    must_fail: bool
    intervals: list[TruthInterval]


def _linear(values: FloatArray) -> FloatArray:
    v = values / 255.0
    return np.where(v < 0.081, v / 4.5, ((v + 0.099) / 1.099) ** (1 / 0.45))


def _uv(values: FloatArray) -> FloatArray:
    matrix = np.array(
        [
            [0.4123907993, 0.3575843394, 0.1804807884],
            [0.2126390059, 0.7151686788, 0.0721923154],
            [0.0193308187, 0.1191947798, 0.9505321522],
        ]
    )
    xyz = values @ matrix.T
    d = xyz[..., 0] + 15 * xyz[..., 1] + 3 * xyz[..., 2]
    return np.stack(
        (
            np.divide(4 * xyz[..., 0], d, out=np.zeros_like(d), where=d > 0),
            np.divide(9 * xyz[..., 1], d, out=np.zeros_like(d), where=d > 0),
        ),
        axis=-1,
    )


def _changes(values: FloatArray, red: bool) -> list[int]:
    # Offline range traversal. Retain both startup endpoints until the first edge.
    edges: list[int] = []
    low = high = values[0].copy()
    direction = 0

    def qualifies(a: FloatArray, b: FloatArray) -> bool:
        if not red:
            return bool(abs(float(a - b)) >= max(20, min(float(a), float(b)) / 8))
        ratios = [float(v[0] / v.sum()) if v.sum() else 0 for v in (a, b)]
        return max(ratios) >= 0.8 and float(np.linalg.norm(_uv(a) - _uv(b))) > 0.2

    for i, value in enumerate(values[1:], 1):
        if red:
            # Color square waves use chromatic distance rather than a scalar ordering.
            reference = high if direction else low
            if qualifies(reference, value):
                edges.append(i)
                high = value.copy()
                direction = 1
            elif not direction and np.linalg.norm(_uv(value) - _uv(low)) > 0:
                high = value.copy()
        elif direction == 0:
            if qualifies(low, value):
                edges.append(i)
                direction = 1 if float(value) > float(low) else -1
                high = value.copy()
            elif qualifies(high, value):
                edges.append(i)
                direction = 1 if float(value) > float(high) else -1
                high = value.copy()
            else:
                low = np.minimum(low, value)
                high = np.maximum(high, value)
        elif direction * float(value - high) >= 0:
            high = value.copy()
        elif qualifies(high, value):
            edges.append(i)
            direction *= -1
            high = value.copy()
    return edges


def _dense_counts(values: FloatArray, fps: int, red: bool = False) -> FloatArray:
    edges = _changes(values, red)
    # Pair opposing edges in observation order; mark close consecutive leading
    # edges, including the prior completed pair, at the time density is established.
    counted: dict[int, int] = {}
    for pair in range(1, (len(edges) + 1) // 2):
        lead, previous = edges[2 * pair], edges[2 * (pair - 1)]
        if (lead - previous) / fps < 0.36 - 1e-9:
            for index in range(2 * (pair - 1), min(2 * pair + 2, len(edges))):
                counted[edges[index]] = min(counted.get(edges[index], lead), lead)
    return np.array(
        [
            sum(
                frame - fps < edge <= frame and available <= frame
                for edge, available in counted.items()
            )
            for frame in range(len(values))
        ]
    )


def _fraction(mask: np.ndarray[tuple[int, ...], np.dtype[np.bool_]], local: bool) -> float:
    if not local:
        return float(mask.mean())
    h, w = mask.shape
    wh, ww = max(1, h // 3), max(1, w // 3)
    table = np.pad(mask.astype(float), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    sums = table[wh:, ww:] - table[:-wh, ww:] - table[wh:, :-ww] + table[:-wh, :-ww]
    return float(sums.max() / (wh * ww))


def oracle(frames: Sequence[ByteArray], fps: int) -> dict[str, ProfileTruth]:
    luminance_frames: list[FloatArray] = []
    color_frames: list[FloatArray] = []
    for frame in frames:
        h, w = frame.shape[:2]
        if frame.ndim == 2:
            y = code10_to_cd_m2(frame.astype(float) * 4)
        else:
            y = code10_to_cd_m2(
                np.rint(16 + 219 * (frame / 255) @ np.array([0.2126, 0.7152, 0.0722])) * 4
            )
            color_frames.append(
                _linear(frame.astype(float)).reshape(h // 4, 4, w // 4, 4, 3).mean((1, 3))
            )
        luminance_frames.append(y.reshape(h // 4, 4, w // 4, 4).mean((1, 3)))
    cells = np.stack(luminance_frames)
    n = len(cells)
    color = np.stack(color_frames) if color_frames else None
    # Unique histories keep scattered-tile ground truth inexpensive and exact.
    histories, inverse = np.unique(cells.reshape(n, -1).T, axis=0, return_inverse=True)
    counts = np.stack([_dense_counts(v, fps) for v in histories])
    luma_counts = counts[inverse].T.reshape(cells.shape)
    red_counts = np.zeros_like(luma_counts)
    if color is not None:
        histories_rgb, inverse_rgb = np.unique(
            color.reshape(n, -1, 3).transpose(1, 0, 2), axis=0, return_inverse=True
        )
        counts_rgb = np.stack([_dense_counts(v, fps, True) for v in histories_rgb])
        red_counts = counts_rgb[inverse_rgb].T.reshape(cells.shape)
    result: dict[str, ProfileTruth] = {}
    for profile, limit in (("broadcast", 6), ("local", 6), ("kids", 4)):
        hot = [
            max(
                _fraction(a > limit, profile != "broadcast"),
                _fraction(b > limit, profile != "broadcast"),
            )
            > 0.25
            for a, b in zip(luma_counts, red_counts, strict=True)
        ]
        intervals: list[TruthInterval] = []
        start: int | None = None
        for index, active in enumerate([*hot, False]):
            if active and start is None:
                start = index
            elif not active and start is not None:
                interval = TruthInterval(t_start=start / fps, t_end=index / fps)
                if intervals and interval.t_start - intervals[-1].t_end < 1:
                    intervals[-1] = TruthInterval(
                        t_start=intervals[-1].t_start, t_end=interval.t_end
                    )
                else:
                    intervals.append(interval)
                start = None
        result[profile] = ProfileTruth(must_fail=bool(intervals), intervals=intervals)
    return result
