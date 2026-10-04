import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from nostrobe.detect.pipeline import detect_arrays
from nostrobe.domain.profiles import get_profile

FPS = (24, 25, 30, 50, 60)
PROFILES = ("broadcast", "local", "kids")


def wave(fps=25, rate=3.5, dark=100, delta=21, duration=3, area=1, pulses=None):
    times = np.arange(round(duration * fps)) / fps
    active = times * rate % 1 >= 0.5
    if pulses is not None:
        active &= (times * rate).astype(int) < pulses
    mask = np.zeros((9, 12), dtype=bool)
    mask.flat[: round(mask.size * area)] = True
    frames = dark + active[:, None, None] * mask * delta
    return frames.astype(float), times


def fails(events):
    return any(e.severity == "fail" for e in events)


@pytest.mark.parametrize("fps", FPS)
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "rate,delta,dark,expected",
    [
        (3, 21, 100, False),
        (3.5, 21, 100, True),
        (3.5, 19, 100, False),
        (3.5, 21, 150, True),
        (3.5, 21, 170, False),
        (1 / 0.34, 21, 100, False),
        (1 / 0.38, 21, 100, False),
    ],
)
def test_rate_luminance_and_spacing(fps, profile, rate, delta, dark, expected):
    frames, times = wave(fps, rate, dark, delta)
    result = detect_arrays(frames, times, [get_profile(profile)])[profile]
    # Kids intentionally has a lower rate limit.
    if profile == "kids" and rate in (3, 1 / 0.34):
        expected = True
    assert fails(result) == expected


@pytest.mark.parametrize("fps", FPS)
@pytest.mark.parametrize("area,expected", [(0.24, False), (0.25, False), (0.26, True)])
def test_global_area_boundary(fps, area, expected):
    times = np.arange(fps * 3) / fps
    mask = np.zeros((10, 10), dtype=bool)
    mask.flat[: round(area * 100)] = True
    frames = 100 + (times * 3.5 % 1 >= 0.5)[:, None, None] * mask * 21
    assert (
        fails(detect_arrays(frames.astype(float), times, [get_profile("broadcast")])["broadcast"])
        == expected
    )


@pytest.mark.parametrize("fps", FPS)
@pytest.mark.parametrize("pulses", (1, 2, 3))
def test_isolated_broadcast_flashes_pass(fps, pulses):
    frames, times = wave(fps, pulses=pulses)
    result = detect_arrays(frames, times)
    assert not fails(result["broadcast"]) and not fails(result["local"])
    if pulses == 3:
        assert fails(result["kids"])


@pytest.mark.parametrize("fps", FPS)
def test_red_rules_and_extended(fps):
    frames, times = wave(fps, delta=0, duration=7)
    rgb = np.zeros((*frames.shape, 3))
    active = times * 3.5 % 1 >= 0.5
    rgb[~active, :, :, 0] = 1
    rgb[active, :, :, 2] = 1
    result = detect_arrays(frames, times, rgb=rgb)
    for profile in PROFILES:
        assert any(e.kind == "red_flash" and e.severity == "fail" for e in result[profile])
        assert any(e.kind == "extended_flashing" and e.severity == "warn" for e in result[profile])
    rgb[:] = [0, 1, 0]
    assert not fails(detect_arrays(frames, times, rgb=rgb)["broadcast"])


@given(
    delta=st.floats(min_value=0, max_value=19.999),
    fps=st.sampled_from(FPS),
    rate=st.floats(min_value=1, max_value=10),
)
@settings(max_examples=35, deadline=None)
def test_subthreshold_luminance_never_fails(delta, fps, rate):
    frames, times = wave(fps, rate=rate, delta=delta)
    assert all(not fails(events) for events in detect_arrays(frames, times).values())


@given(pulses=st.integers(1, 3), fps=st.sampled_from(FPS), gap=st.floats(1.1, 2.5))
@settings(max_examples=20, deadline=None)
def test_separated_isolated_bursts_never_add_broadcast_fail(pulses, fps, gap):
    frames, times = wave(fps, pulses=pulses)
    pause = np.full((round(gap * fps), *frames.shape[1:]), 100.0)
    joined = np.concatenate((frames, pause, frames))
    times = np.arange(len(joined)) / fps
    assert not fails(detect_arrays(joined, times, [get_profile("broadcast")])["broadcast"])


def test_monotone_luminance_does_not_count_as_flashes():
    frames = np.broadcast_to(np.linspace(0, 159, 60)[:, None, None], (60, 9, 12))
    assert not detect_arrays(frames, np.arange(60) / 60)["broadcast"]
