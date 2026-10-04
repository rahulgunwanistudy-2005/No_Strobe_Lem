"""Canonical HazardTrack JSON with a strict publication/read gate."""

from pathlib import Path

from nostrobe.domain.models import HazardTrack
from nostrobe.errors import VerifierFailedError


def require_verified(track: HazardTrack) -> None:
    if not track.verifier.passes or track.verifier.residual_events:
        raise VerifierFailedError("track has unresolved verification failures")


def serialize(track: HazardTrack, *, allow_unresolved: bool = False) -> str:
    track = HazardTrack.model_validate(track.model_dump())
    if not allow_unresolved:
        require_verified(track)
    return track.model_dump_json(indent=2) + "\n"


def parse(payload: str, *, allow_unresolved: bool = False) -> HazardTrack:
    track = HazardTrack.model_validate_json(payload)
    if not allow_unresolved:
        require_verified(track)
    return track


def write(path: Path, track: HazardTrack) -> None:
    unresolved = path.name.endswith(".unresolved.hzt.json")
    if not track.verifier.passes and not unresolved:
        require_verified(track)
    path.write_text(serialize(track, allow_unresolved=unresolved))
