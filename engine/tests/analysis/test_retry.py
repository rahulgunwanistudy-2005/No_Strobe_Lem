import numpy as np
import pytest

from nostrobe.analysis import analyze_cache
from nostrobe.decode.cache import FrameCache
from nostrobe.domain.profiles import get_profile
from nostrobe.veil.solver import SolveResult


@pytest.mark.parametrize("final_pass", [True, False])
def test_full_verification_retries_once_preserving_source_provenance(
    track, tmp_path, monkeypatch, final_pass
):
    from nostrobe import analysis

    cache = FrameCache(track.media, tmp_path, np.array([0.0, 0.5]), ())
    params = get_profile("broadcast")
    monkeypatch.setattr(analysis, "detect_cached", lambda *args: {"broadcast": track.events})
    calls = []

    def solver(cache, events, params):
        calls.append(list(events))
        cue = track.veils[0]
        if len(calls) > 1:
            cue = cue.model_copy(update={"covers": [e.id for e in events]})
        return SolveResult([cue], [])

    monkeypatch.setattr(analysis, "solve", solver)
    residual = track.events[0].model_copy(update={"id": "residual", "t_start": 0.3, "t_end": 0.5})
    failed = track.verifier.model_copy(update={"passes": False, "residual_events": [residual]})
    outcomes = iter([failed, track.verifier if final_pass else failed])
    monkeypatch.setattr(analysis, "verify", lambda *args: next(outcomes))
    monkeypatch.setattr(analysis, "distortion", lambda *args: 1.0)
    result = analyze_cache(cache, [params])[0]
    assert len(calls) == 2 and len(calls[1]) == len(track.events) + 1
    assert result.events == track.events
    assert result.veils[0].covers == [track.events[0].id]
    assert result.verifier.passes == final_pass
    if not final_pass:
        assert result.unresolved_segments and result.unresolved_segments[0].reason
