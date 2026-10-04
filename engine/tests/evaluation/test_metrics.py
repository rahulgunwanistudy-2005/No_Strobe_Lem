from nostrobe.domain.models import HazardEvent
from nostrobe.evaluation.metrics import Observation, interval_iou, summarize
from nostrobe.evaluation.truth import ProfileTruth
from nostrobe.synth.generator import TruthInterval


def event(start, end):
    return HazardEvent(
        id="evt_0001",
        kind="luma_flash",
        severity="fail",
        t_start=start,
        t_end=end,
        peak_changes_per_s=8,
        peak_area_fraction=1,
        peak_delta_cd_m2=60,
        regime="absolute",
    )


def test_union_iou_does_not_double_count_overlapping_kinds():
    assert interval_iou([event(1, 3), event(2, 4)], [TruthInterval(t_start=2, t_end=5)]) == 0.5
    assert interval_iou([], []) == 1
    assert interval_iou([], [TruthInterval(t_start=0, t_end=1)]) == 0


def test_confusion_distinguishes_all_four_outcomes_and_excludes_clean():
    rows = []
    for i, (expected, actual) in enumerate(
        [(True, True), (False, False), (True, False), (False, True)]
    ):
        rows.append(
            Observation(
                suite="boundary",
                name=str(i),
                profile="broadcast",
                source_sha256="0" * 64,
                duration_s=2,
                truth=ProfileTruth(
                    must_fail=expected,
                    intervals=[TruthInterval(t_start=0, t_end=1)] if expected else [],
                ),
                events=[event(0, 1)] if actual else [],
                track=None,
                detect_s=1,
                analyze_s=None,
                decode_s=1,
            )
        )
    rows.append(rows[0].model_copy(update={"suite": "clean", "truth": None}))
    value = summarize(rows)["broadcast"]
    assert value["confusion"] == dict(tp=1, tn=1, fp=1, fn=1)
    assert not value["gate_passes"]
