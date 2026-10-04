"""Typed scaffold for a gated later session."""

from nostrobe.domain.models import HazardEvent


def merge_events(events: list[HazardEvent], merge_gap_s: float) -> list[HazardEvent]:
    raise NotImplementedError("event merging begins in S2")
