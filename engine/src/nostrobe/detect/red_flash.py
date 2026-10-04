"""Typed scaffold for a gated later session."""

from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


def detect_red(
    frames: FloatArray, timestamps: FloatArray, params: ProfileParams
) -> list[HazardEvent]:
    raise NotImplementedError("red detector begins in S2")
