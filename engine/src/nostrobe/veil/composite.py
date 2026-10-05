"""Display-code blending and deterministic HazardTrack playback semantics."""

import math
from collections.abc import Sequence
from functools import lru_cache

import numpy as np

from nostrobe.domain.models import VeilCue
from nostrobe.luminance.curve import FloatArray


def composite(frames: FloatArray, alpha: float, gray: float) -> FloatArray:
    if not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("alpha must be finite and in [0, 1]")
    if not math.isfinite(gray) or not 0 <= gray <= 1:
        raise ValueError("gray must be finite and in [0, 1]")
    if not np.all(np.isfinite(frames)) or np.any((frames < 0) | (frames > 1)):
        raise ValueError("display codes must be finite and normalized")
    return np.asarray((1 - alpha) * frames + alpha * gray, dtype=np.float64)


def apply_veil(
    luma_code_norm: FloatArray, rgb_norm: FloatArray, alpha: float, gray: float
) -> tuple[FloatArray, FloatArray]:
    if rgb_norm.shape != (*luma_code_norm.shape, 3):
        raise ValueError("RGB shape must match luma with three channels")
    display_gray = veil_gray(gray)
    return composite(luma_code_norm, alpha, (16 + 219 * display_gray) / 255), composite(
        rgb_norm, alpha, display_gray
    )


def veil_gray(gray: float) -> float:
    """Vega View's RGB code, matching Math.round(gray * 255)."""
    if not math.isfinite(gray) or not 0 <= gray <= 1:
        raise ValueError("gray must be finite and in [0, 1]")
    return math.floor(gray * 255 + 0.5) / 255


@lru_cache(maxsize=1024)
def composite_luts(alpha: float, gray: float) -> tuple[FloatArray, FloatArray]:
    """Separate decoded limited BT.709 Y and full-range RGB display-code LUTs."""
    codes = np.arange(256, dtype=np.float64) / 255
    display_gray = veil_gray(gray)
    y = composite(codes, alpha, (16 + 219 * display_gray) / 255)
    rgb = composite(codes, alpha, display_gray)
    y.flags.writeable = rgb.flags.writeable = False
    return y, rgb


def veil_timeline(cues: Sequence[VeilCue], t: float) -> tuple[float, float]:
    """Linear ramps; overlap uses strongest opacity, then lower gray/id."""
    if not math.isfinite(t):
        raise ValueError("timeline time must be finite")
    active: list[tuple[float, float, str]] = []
    for cue in cues:
        strength = min(
            1.0,
            (t - cue.t_on + cue.ramp_in_s) / cue.ramp_in_s,
            (cue.t_off + cue.ramp_out_s - t) / cue.ramp_out_s,
        )
        alpha = cue.alpha * max(0.0, strength)
        if alpha > 0:
            active.append((alpha, cue.gray, cue.id))
    if not active:
        return 0.0, 0.0
    alpha, gray, _ = min(active, key=lambda item: (-item[0], item[1], item[2]))
    return alpha, gray
