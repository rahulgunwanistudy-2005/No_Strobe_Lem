import numpy as np
import pytest

from nostrobe.domain.profiles import get_profile
from nostrobe.veil.composite import apply_veil, composite, veil_timeline
from nostrobe.veil.segments import segments


def test_composite_identity_gray_and_validation():
    y = np.array([[0.0, 0.5, 1.0]])
    rgb = np.repeat(y[..., None], 3, axis=-1)
    a, b = apply_veil(y, rgb, 0, 0.25)
    np.testing.assert_array_equal(a, y)
    np.testing.assert_array_equal(b, rgb)
    a, b = apply_veil(y, rgb, 1, 0.25)
    assert np.all(a == 0.25) and np.all(b == 0.25)
    for alpha, gray in ((-0.1, 0), (1.1, 0), (0, -1), (0, np.nan)):
        with pytest.raises(ValueError):
            composite(y, alpha, gray)
    with pytest.raises(ValueError):
        composite(np.array([np.inf]), 0.5, 0.5)


def test_linear_continuous_ramps_and_support(track):
    cue = track.veils[0]
    cue = cue.model_copy(update={"t_on": 1.0, "t_off": 2.0, "alpha": 0.8, "gray": 0.25})
    for t, alpha in (
        (0.49, 0),
        (0.5, 0),
        (0.75, 0.4),
        (1.0, 0.8),
        (2.0, 0.8),
        (2.25, 0.4),
        (2.5, 0),
    ):
        assert veil_timeline([cue], t)[0] == pytest.approx(alpha)
    for t in (1.0, 2.0):
        assert abs(veil_timeline([cue], t - 1e-9)[0] - veil_timeline([cue], t + 1e-9)[0]) < 1e-8
    other = cue.model_copy(update={"id": "other", "gray": 0.5})
    assert veil_timeline([other, cue], 1.5) == (0.8, 0.25)
    assert veil_timeline([cue, other], 1.5) == (0.8, 0.25)


def test_segment_boundaries_merging_and_warning_policy(track):
    params = get_profile("broadcast")
    original = track.events[0]
    events = [
        original.model_copy(update={"id": "a", "t_start": 0.0, "t_end": 0.5}),
        original.model_copy(update={"id": "b", "t_start": 1.0, "t_end": 2.0}),
        original.model_copy(update={"id": "c", "t_start": 4.5, "t_end": 5.0}),
    ]
    found = segments(events, 5.0, params)
    assert [(s.start, s.end, s.covers) for s in found] == [
        (0.0, 2.25, ("a", "b")),
        (4.25, 5.0, ("c",)),
    ]
    for s in found:
        cue = s.cue(1, 0.5, 0.25, params)
        for t in (-1.0, 6.0):
            assert veil_timeline([cue], t)[0] == 0
    warnings = [original.model_copy(update={"severity": "warn"})]
    assert not segments(warnings, 5.0, params)
    assert segments(warnings, 5.0, get_profile("kids"))
