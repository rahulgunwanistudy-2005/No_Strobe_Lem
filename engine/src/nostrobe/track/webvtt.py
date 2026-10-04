"""Strict metadata WebVTT; VeilCue payloads retain exact float values."""

import json
import math
import re

from nostrobe.domain.models import HazardTrack, VeilCue
from nostrobe.track.jsonio import require_verified

_TIMING = re.compile(r"^(\d{2,}):([0-5]\d):([0-5]\d)\.(\d{3})$")


def timestamp(t: float) -> str:
    if not math.isfinite(t):
        raise ValueError("timestamp must be finite")
    milliseconds = max(0, math.floor(t * 1000 + 0.5))
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def _seconds(value: str) -> float:
    match = _TIMING.fullmatch(value)
    if match is None:
        raise ValueError("invalid WebVTT timestamp")
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000


def serialize(track: HazardTrack) -> str:
    track = HazardTrack.model_validate(track.model_dump())
    require_verified(track)
    metadata = track.model_dump(mode="json", exclude={"events", "veils"})
    # A separate NOTE retains event provenance without changing the metadata contract.
    events = [event.model_dump(mode="json") for event in track.events]
    blocks = [
        "WEBVTT",
        "NOTE hazardtrack\n" + json.dumps(metadata, separators=(",", ":")),
        "NOTE hazardtrack-events\n" + json.dumps(events, separators=(",", ":")),
    ]
    for cue in sorted(track.veils, key=lambda c: (c.t_on - c.ramp_in_s, c.id)):
        start = timestamp(cue.t_on - cue.ramp_in_s)
        end = timestamp(cue.t_off + cue.ramp_out_s)
        if _seconds(end) <= _seconds(start):
            raise ValueError("WebVTT cue has no positive duration")
        blocks.append(f"{cue.id}\n{start} --> {end}\n{cue.model_dump_json()}")
    return "\n\n".join(blocks) + "\n\n"


def parse(payload: str) -> HazardTrack:
    blocks = payload.removeprefix("\ufeff").replace("\r\n", "\n").strip().split("\n\n")
    if not blocks or blocks[0] != "WEBVTT":
        raise ValueError("missing WEBVTT header")
    metadata: dict[str, object] | None = None
    events: list[object] = []
    event_note = False
    cues: list[VeilCue] = []
    previous = -1.0
    for block in blocks[1:]:
        lines = block.splitlines()
        if lines[0] == "NOTE hazardtrack":
            if metadata is not None or len(lines) != 2:
                raise ValueError("duplicate or malformed metadata")
            value = json.loads(lines[1])
            if not isinstance(value, dict):
                raise ValueError("metadata must be an object")
            metadata = value
        elif lines[0] == "NOTE hazardtrack-events":
            if event_note or len(lines) != 2:
                raise ValueError("duplicate or malformed event note")
            value = json.loads(lines[1])
            if not isinstance(value, list):
                raise ValueError("events must be an array")
            events, event_note = value, True
        elif lines[0].startswith("NOTE"):
            continue
        else:
            if len(lines) != 3 or " --> " not in lines[1]:
                raise ValueError("malformed WebVTT cue")
            start_text, end_text = lines[1].split(" --> ")
            start, end = _seconds(start_text), _seconds(end_text)
            cue = VeilCue.model_validate_json(lines[2])
            if lines[0] != cue.id or end <= start or start < previous:
                raise ValueError("invalid cue identity, duration or ordering")
            if start_text != timestamp(cue.t_on - cue.ramp_in_s) or end_text != timestamp(
                cue.t_off + cue.ramp_out_s
            ):
                raise ValueError("cue timing does not match its payload")
            previous = start
            cues.append(cue)
    if metadata is None:
        raise ValueError("missing HazardTrack metadata")
    if not event_note and any(c.covers for c in cues):
        raise ValueError("event provenance required for covered cues")
    track = HazardTrack.model_validate(metadata | {"events": events, "veils": cues})
    require_verified(track)
    return track
