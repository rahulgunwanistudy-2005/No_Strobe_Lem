from dataclasses import replace

import pytest

from nostrobe.evaluation.suites import boundary_specs, shape_specs
from nostrobe.evaluation.truth import oracle
from nostrobe.synth.generator import analytic_truth, iter_frames, smoke_specs


@pytest.mark.parametrize("fps", [24, 25, 30, 50, 60])
def test_original_s1_broadcast_truth_is_preserved(fps):
    for original in smoke_specs():
        spec = replace(original, fps=fps)
        truth = oracle(list(iter_frames(spec)), fps)
        assert truth["broadcast"].must_fail == (analytic_truth(spec).label == "must_fail"), (
            spec.name
        )
        if spec.name == "area_24":
            assert truth["local"].must_fail
        if spec.name == "isolated_3":
            assert truth["kids"].must_fail


def test_seeded_suite_coverage():
    first = shape_specs(7, 200, [24, 25, 30, 50, 60])
    assert first == shape_specs(7, 200, [24, 25, 30, 50, 60])
    assert first != shape_specs(8, 200, [24, 25, 30, 50, 60])
    assert len({s.name for s in first}) == 200
    assert len({s.primitive for s in first}) == 10
    assert {s.fps for s in boundary_specs(7, [24, 25, 30, 50, 60])} == {24, 25, 30, 50, 60}


def test_sdr_oracle_uses_published_regime_not_hdr_relative_helper():
    import numpy as np

    from nostrobe.evaluation.truth import _changes

    assert _changes(np.array([159.0, 190.0, 159.0]), False) == [1, 2]
    assert _changes(np.array([160.0, 200.0, 160.0]), False) == []
    assert _changes(np.array([170.0, 198.0, 170.0]), False) == []
    # High-dark cases remain in the suite; no seed, amplitude or truth interval
    # is adjusted to match production output.
    specs = shape_specs(7, 200, [24, 25, 30, 50, 60])
    for index in (14, 24, 34):
        spec = specs[index]
        assert spec.dark_cd_m2 == 170 and spec.delta_cd_m2 == 28
        truth = oracle(list(iter_frames(spec)), spec.fps)
        assert not any(v.must_fail for v in truth.values())
