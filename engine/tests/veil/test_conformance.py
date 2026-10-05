import json
from pathlib import Path

from nostrobe.veil.conformance import timeline_fixture


def test_shared_fixture_has_no_drift() -> None:
    path = Path(__file__).resolve().parents[3] / "spec/examples/timeline_conformance.json"
    assert json.loads(path.read_text()) == timeline_fixture()
    assert len(timeline_fixture()["samples"]) == 500
