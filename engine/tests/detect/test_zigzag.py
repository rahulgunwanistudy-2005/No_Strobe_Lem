import numpy as np
import pytest

from nostrobe.detect.rate import FlashCounter
from nostrobe.detect.zigzag import ChangeDetector, TimestampRing, sdr_threshold
from nostrobe.luminance.curve import thr


def crossings(values, threshold=thr):
    detector = ChangeDetector((1, 1), threshold)
    return [
        bool(detector.update(np.array([[v]], dtype=np.float32), i / 60)[0, 0])
        for i, v in enumerate(values)
    ]


def test_monotone_thresholds_and_square_wave():
    assert crossings(range(100)) == [i > 0 and i % 20 == 0 for i in range(100)]
    assert crossings([100, 121] * 10) == [False] + [True] * 19
    assert not any(crossings([100, 119] * 10))
    assert crossings([150, 170, 150]) == [False, True, True]
    assert not any(crossings([170, 191, 170]))
    assert crossings([170, 192, 170]) == [False, True, True]
    assert not any(crossings([160, 181, 160], sdr_threshold))
    assert crossings([159, 180, 159], sdr_threshold) == [False, True, True]


def test_running_extreme_and_noise():
    assert crossings([100, 125, 140, 121, 120]) == [False, True, False, False, True]
    noise = np.random.default_rng(7).normal(100, 3, 180)
    assert not any(crossings(noise))
    assert thr(np.array([159.999, 160, 160.001])).tolist() == pytest.approx([20, 20, 20.000125])


def test_ring_expiry_per_cell_wrap_and_overflow():
    ring = TimestampRing((2, 2), capacity=8)
    mask = np.array([[True, False], [False, True]])
    for index in range(8):
        ring.add(mask, index / 10)
    with pytest.raises(ValueError, match="capacity"):
        ring.add(mask, 0.9)
    ring.expire(1)
    np.testing.assert_array_equal(ring.counts, [[7, 0], [0, 7]])
    ring.add(~mask, 1.1)
    ring.expire(2)
    np.testing.assert_array_equal(ring.counts, [[0, 1], [1, 0]])
    ring.expire(2.1)
    assert not ring.counts.any()


def test_counter_spacing_exact_window_and_monotone():
    mask = np.ones((1, 1), dtype=bool)
    for spacing, expected in [(0.34, 6), (0.36, 0), (0.38, 0)]:
        counter = FlashCounter((1, 1))
        for i, time in enumerate([0, 0.1, spacing, spacing + 0.1, 2 * spacing, 2 * spacing + 0.1]):
            counts, raw = counter.update(mask, np.full((1, 1), 1 if i % 2 == 0 else -1), time)
        assert counts.item() == expected
        assert raw.item() == 6
    counter = FlashCounter((1, 1))
    for i in range(20):
        counts, raw = counter.update(mask, np.ones((1, 1), dtype=np.int8), i / 100)
    assert counts.item() == 0 and raw.item() == 1


@pytest.mark.parametrize("value,time", [(np.nan, 0), (-1, 0), (1, np.nan), (1, -1)])
def test_invalid_input(value, time):
    with pytest.raises(ValueError):
        ChangeDetector((1, 1)).update(np.array([[value]]), time)
