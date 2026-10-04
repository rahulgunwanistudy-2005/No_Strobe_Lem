import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nostrobe.config import Settings
from nostrobe.domain.models import HazardEvent, HazardTrack, VeilCue, VerifierResult
from nostrobe.domain.schema import schema_text


def test_json_round_trip_and_ignored_extensions(track: HazardTrack) -> None:
    payload = track.model_dump(mode="json")
    payload["future_extension"] = {"ignored": True}
    assert HazardTrack.model_validate_json(json.dumps(payload)) == track


@pytest.mark.parametrize("end", [0, 1, float("nan"), float("inf")])
def test_event_end_invalid(track: HazardTrack, end: float) -> None:
    payload = track.events[0].model_dump() | {"t_end": end}
    with pytest.raises(ValidationError):
        HazardEvent.model_validate(payload)


@pytest.mark.parametrize("field", ["alpha", "gray"])
@pytest.mark.parametrize("value", [-0.01, 1.01, float("nan"), float("inf")])
def test_veil_fraction_bounds(track: HazardTrack, field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        VeilCue.model_validate(track.veils[0].model_dump() | {field: value})


def test_frozen_and_timestamps(track: HazardTrack) -> None:
    with pytest.raises(ValidationError):
        track.profile = "kids"
    with pytest.raises(ValidationError):
        HazardTrack.model_validate(track.model_dump() | {"generated_at": datetime(2026, 10, 4)})
    aware = datetime(2026, 10, 4, 5, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    assert (
        HazardTrack.model_validate(track.model_dump() | {"generated_at": aware}).generated_at.hour
        == 0
    )


def test_verifier_inconsistent_pass(track: HazardTrack) -> None:
    for updates in ({"residual_events": track.events}, {"offsets_checked_s": []}):
        with pytest.raises(ValidationError):
            VerifierResult.model_validate(track.verifier.model_dump() | updates)


def test_missing_reference(track: HazardTrack) -> None:
    payload = track.model_dump()
    payload["veils"][0]["covers"] = ["missing"]
    with pytest.raises(ValidationError):
        HazardTrack.model_validate(payload)


def test_schema_does_not_drift() -> None:
    assert Settings().schema_path.read_text() == schema_text()


def test_generated_types_do_not_drift() -> None:
    root = Settings().repo_root
    subprocess.run(["node", "scripts/generate-types.cjs", "--check"], cwd=root, check=True)


def test_schema_cli(tmp_path: Path) -> None:
    target = tmp_path / "schema.json"
    subprocess.run(
        [sys.executable, "-m", "nostrobe.cli", "schema", "--output", str(target)], check=True
    )
    assert target.read_text() == schema_text()
