"""Deterministic playback oracle shared by Python and TypeScript readers."""

import json
from pathlib import Path

import numpy as np

from nostrobe.domain.models import VeilCue
from nostrobe.veil.composite import veil_timeline


def timeline_fixture() -> dict[str, object]:
    cues = [
        VeilCue(
            id="early",
            t_on=0,
            t_off=1,
            ramp_in_s=0.5,
            ramp_out_s=0.75,
            alpha=0.6,
            gray=0.5,
            covers=[],
        ),
        VeilCue(
            id="overlap",
            t_on=1.5,
            t_off=3,
            ramp_in_s=1,
            ramp_out_s=0.5,
            alpha=0.8,
            gray=0.25,
            covers=[],
        ),
        VeilCue(
            id="tie-b",
            t_on=4,
            t_off=5,
            ramp_in_s=0.5,
            ramp_out_s=0.5,
            alpha=0.7,
            gray=0.5,
            covers=[],
        ),
        VeilCue(
            id="tie-a",
            t_on=4,
            t_off=5,
            ramp_in_s=0.5,
            ramp_out_s=0.5,
            alpha=0.7,
            gray=0.25,
            covers=[],
        ),
        VeilCue(
            id="end",
            t_on=8,
            t_off=10,
            ramp_in_s=0.5,
            ramp_out_s=1,
            alpha=0.85,
            gray=0.25,
            covers=[],
        ),
    ]
    boundaries = [-1, -0.5, 0, 0.5, 1, 1.5, 1.75, 3, 3.5, 4, 5, 5.5, 7.5, 8, 10, 11, 12]
    times = sorted(boundaries + np.linspace(-1, 12, 500 - len(boundaries)).tolist())
    return {
        "format": "hazardtrack-timeline-conformance",
        "version": 1,
        "duration_s": 10,
        "cues": [cue.model_dump() for cue in cues],
        "samples": [
            {"time": t, "alpha": veil_timeline(cues, t)[0], "gray": veil_timeline(cues, t)[1]}
            for t in times
        ],
        "playback_cases": [
            {
                "action": action,
                "time": t,
                "alpha": veil_timeline(cues, t)[0],
                "gray": veil_timeline(cues, t)[1],
            }
            for action, t in [("seek", 2), ("pause", 2), ("seek", 0), ("end", 10)]
        ],
    }


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[4] / "spec/examples/timeline_conformance.json"
    destination.write_text(json.dumps(timeline_fixture(), indent=2) + "\n")
