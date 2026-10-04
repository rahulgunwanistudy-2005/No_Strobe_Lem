"""Typed scaffold for a gated later session."""

from nostrobe.domain.models import HazardEvent, VeilCue
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


def solve(frames: FloatArray, events: list[HazardEvent], params: ProfileParams) -> list[VeilCue]:
    raise NotImplementedError("veil solver begins in S3")
