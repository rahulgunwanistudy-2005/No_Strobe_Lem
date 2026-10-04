"""Track serialization scaffold for S3."""

from nostrobe.domain.models import HazardTrack


def serialize(track: HazardTrack) -> str:
    raise NotImplementedError("track writer begins in S3")


def parse(payload: str) -> HazardTrack:
    raise NotImplementedError("track reader begins in S3")
