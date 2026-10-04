import numpy as np
import pytest

from nostrobe.detect.area import global_fraction, max_local_fraction
from nostrobe.detect.events import EventBuilder, FrameEvidence, merge_events
from nostrobe.detect.extended import ExtendedDetector
from nostrobe.domain.models import HazardEvent
from nostrobe.domain.profiles import get_profile


def test_global_and_local_borders():
    mask = np.zeros((90, 160), dtype=bool)
    assert global_fraction(mask) == max_local_fraction(mask) == 0
    mask[-30:, -53:] = True
    assert max_local_fraction(mask) == 1
    assert global_fraction(mask) == 1590 / 14400
    rng = np.random.default_rng(7)
    small = rng.random((9, 12)) < 0.3
    expected = max(small[y : y + 3, x : x + 4].mean() for y in range(7) for x in range(9))
    assert max_local_fraction(small, (3, 4)) == expected
    with pytest.raises(ValueError):
        max_local_fraction(small, (10, 1))


def event(start, end, severity="fail", kind="luma_flash", area=0.3, count=7):
    return HazardEvent(
        id="test",
        kind=kind,
        severity=severity,
        t_start=start,
        t_end=end,
        peak_changes_per_s=count,
        peak_area_fraction=area,
        peak_delta_cd_m2=21,
        regime="absolute",
    )


def test_merge_gaps_strict_and_peak_stats():
    items = [
        event(4, 5),
        event(0, 1),
        event(1.9, 3, count=9, area=0.8),
        event(0.5, 2.5, severity="warn"),
    ]
    merged = merge_events(items, 1)
    assert len(merged) == 3
    assert [(e.t_start, e.t_end) for e in merged if e.severity == "fail"] == [(0, 3), (4, 5)]
    assert merged[0].peak_changes_per_s == 9 and merged[0].peak_area_fraction == 0.8
    assert len({e.id for e in merged}) == 3


def test_event_builder_variable_timestamps_and_severity():
    builder = EventBuilder("luma_flash", 0)
    for time, severity in [(0, None), (0.11, "warn"), (0.24, "fail"), (0.4, "fail"), (0.61, None)]:
        builder.update(FrameEvidence(time, severity, 7, 0.4, 21))
    events = builder.finish(0.9)
    assert [(e.t_start, e.t_end, e.severity) for e in events] == [
        (0.11, 0.24, "warn"),
        (0.24, 0.61, "fail"),
    ]


def test_extended_strict_duration_reset_and_warn_only():
    detector = ExtendedDetector(get_profile("broadcast"))
    counts = np.full((3, 3), 3, dtype=np.int64)
    assert detector.update(counts, 0).severity is None
    assert detector.update(counts, 5).severity is None
    assert detector.update(counts, 5.01).severity == "warn"
    assert detector.update(counts * 0, 5.1).severity is None
    assert detector.update(counts, 5.2).severity is None
