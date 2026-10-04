import pytest

from nostrobe.errors import VerifierFailedError
from nostrobe.track import jsonio, webvtt
from nostrobe.track.stats import track_stats


def test_lossless_roundtrip(track):
    assert jsonio.parse(jsonio.serialize(track)) == track
    text = webvtt.serialize(track)
    assert webvtt.parse(text) == track
    assert "WEBVTT\n\nNOTE hazardtrack\n" in text
    assert webvtt.timestamp(3599.9996) == "01:00:00.000"
    assert webvtt.timestamp(-0.5) == "00:00:00.000"


def test_unresolved_publication_and_read_refusal(track, tmp_path):
    failed = track.model_copy(
        update={"verifier": track.verifier.model_copy(update={"passes": False})}
    )
    for writer in (jsonio.serialize, webvtt.serialize):
        with pytest.raises(VerifierFailedError):
            writer(failed)
    text = jsonio.serialize(failed, allow_unresolved=True)
    with pytest.raises(VerifierFailedError):
        jsonio.parse(text)
    assert jsonio.parse(text, allow_unresolved=True) == failed
    with pytest.raises(VerifierFailedError):
        jsonio.write(tmp_path / "bad.hzt.json", failed)
    jsonio.write(tmp_path / "bad.unresolved.hzt.json", failed)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.replace("WEBVTT", "VTT", 1),
        lambda s: s.replace(" --> ", " -> "),
        lambda s: s.replace("00:00:", "00:61:", 1),
        lambda s: s.replace("NOTE hazardtrack\n", "NOTE other\n", 1),
    ],
)
def test_strict_parser_rejects_invalid_vtt(track, mutation):
    with pytest.raises(ValueError):
        webvtt.parse(mutation(webvtt.serialize(track)))


def test_stats_integrate_ramps_and_overlap(track):
    cue = track.veils[0].model_copy(update={"t_on": 1.0, "t_off": 2.0, "alpha": 0.8})
    stats = track_stats(track.events, [cue, cue.model_copy(update={"id": "second"})], 4.0)
    assert stats.veiled_fraction_of_runtime == pytest.approx(0.5)
    assert stats.mean_alpha == pytest.approx(0.6)
    assert stats.n_events_by_kind == {track.events[0].kind: 1}
