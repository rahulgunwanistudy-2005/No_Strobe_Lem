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
