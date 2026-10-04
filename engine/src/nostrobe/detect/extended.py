"""Typed scaffold for a gated later session."""

from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


def detect_extended(
    frames: FloatArray, timestamps: FloatArray, params: ProfileParams
) -> list[HazardEvent]:
    raise NotImplementedError("extended detector begins in S2")
