"""Report scaffold for S3."""

from nostrobe.domain.models import HazardTrack


def render(track: HazardTrack) -> str:
    raise NotImplementedError("HTML report begins in S3")
