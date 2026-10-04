"""Typed scaffold for a gated later session."""

from nostrobe.domain.models import VeilCue, VerifierResult
from nostrobe.domain.profiles import ProfileParams
from nostrobe.luminance.curve import FloatArray


def verify(frames: FloatArray, cues: list[VeilCue], params: ProfileParams) -> VerifierResult:
    raise NotImplementedError("closed-loop verifier begins in S3")
