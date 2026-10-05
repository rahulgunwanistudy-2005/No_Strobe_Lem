from dataclasses import replace

import numpy as np
import pytest

from nostrobe.config import Settings
from nostrobe.decode.cache import load_cache
from nostrobe.decode.ffmpeg import block_mean
from nostrobe.detect.pipeline import analyze_detect_all
from nostrobe.domain.profiles import get_profile
from nostrobe.luminance.color import bt709_to_linear
from nostrobe.luminance.curve import code10_to_cd_m2
from nostrobe.synth.generator import ClipSpec, encode
from nostrobe.veil.composite import apply_veil
from nostrobe.veil.solver import solve
from nostrobe.verify.verifier import detect_cached, verify


def test_cache_exact_pre_average_composite_and_reuse(tmp_path):
    path = tmp_path / "HAZARD_checker.mp4"
    encode(path, ClipSpec("checker", "checker", duration_s=0.2))
    config = Settings(repo_root=tmp_path)
    cache = load_cache(path, config)
    assert load_cache(path, config).directory == cache.directory
    frame, _ = next(cache.samples())
    luma, rgb = cache.cells(frame, 0.4, 0.25)
    y, color = apply_veil(
        frame[..., 0].astype(float) / 255, frame[..., 1:].astype(float) / 255, 0.4, 0.25
    )
    np.testing.assert_allclose(luma, block_mean(code10_to_cd_m2(y * 255 * 4)))
    np.testing.assert_allclose(rgb, block_mean(bt709_to_linear(color)))
    assert (
        detect_cached(cache, [], [get_profile("broadcast")])["broadcast"]
        == analyze_detect_all(path)["broadcast"]
    )


def test_closed_loop_ramps_offsets_and_unresolved(tmp_path):
    path = tmp_path / "HAZARD_flash.mp4"
    encode(path, ClipSpec("flash", "full_flash"))
    cache = load_cache(path, Settings(repo_root=tmp_path))
    params = get_profile("broadcast")
    events = detect_cached(cache, [], [params])["broadcast"]
    assert not verify(cache, [], params).passes
    result = solve(cache, events, params)
    assert result.cues and not result.unresolved
    checked = verify(cache, result.cues, params)
    assert checked.passes and checked.offsets_checked_s == [
        -params.sync_tolerance_s,
        0.0,
        params.sync_tolerance_s,
    ]
    assert not checked.residual_events
    too_weak = solve(cache, events, replace(params, max_alpha=0.02))
    assert too_weak.unresolved and too_weak.cues[0].alpha == 0.02
    assert too_weak.unresolved[0].reason
    assert not verify(cache, too_weak.cues, params).passes
    with pytest.raises(ValueError):
        verify(cache, result.cues, params, [])


@pytest.mark.parametrize(
    "primitive,area", [("regional_rect", 0.26), ("regional_tiles", 0.26), ("red", 1.0)]
)
def test_exact_cell_grouping_preserves_area_and_all_profiles(tmp_path, primitive, area):
    path = tmp_path / "HAZARD_grouped.mp4"
    encode(path, ClipSpec("grouped", primitive, area=area, duration_s=1.5))
    cache = load_cache(path, Settings(repo_root=tmp_path))
    grouping = cache.grouping(0, cache.media.duration_s)
    assert grouping is not None
    indices, mapping = grouping
    for frame, _t in cache.samples():
        for alpha, gray in ((0.0, 0.0), (0.36, 0.25)):
            original, color = cache.cells(frame, alpha, gray)
            reduced, reduced_color = cache.grouped_cells(frame, indices, alpha, gray)
            np.testing.assert_array_equal(original, reduced.reshape(-1)[mapping])
            np.testing.assert_array_equal(color, reduced_color.reshape(-1, 3)[mapping])
    params = [get_profile(p) for p in ("broadcast", "local", "kids")]
    ordinary = detect_cached(cache, [], params)
    grouped = detect_cached(cache, [], params, bounds=(0, cache.media.duration_s))
    assert ordinary == grouped


def test_kids_extended_warning_is_not_hidden_by_short_context(tmp_path, monkeypatch):
    path = tmp_path / "HAZARD_extended.mp4"
    encode(path, ClipSpec("extended", "full_flash", rate=2, duration_s=7))
    cache = load_cache(path, Settings(repo_root=tmp_path))
    kids = get_profile("kids")
    events = detect_cached(cache, [], [kids])["kids"]
    assert any(e.kind == "extended_flashing" for e in events)
    assert not any(e.severity == "fail" for e in events)
    result = solve(cache, events, kids)
    assert result.cues and result.cues[0].alpha == kids.max_alpha
    # Fixed lead/ramp padding is too late to clear the trailing change window.
    # The required outcome is explicit refusal, never a zero-opacity "pass".
    assert result.unresolved and result.unresolved[0].covers == [events[0].id]
    strict = verify(cache, result.cues, kids, reject_warnings=True)
    assert not strict.passes
    assert any(e.kind == "extended_flashing" for e in strict.residual_events)
    assert verify(cache, result.cues, kids).passes
    from nostrobe import analysis

    monkeypatch.setattr(analysis, "solve", lambda *args: result)
    track = analysis.analyze_cache(cache, [kids])[0]
    assert not track.verifier.passes and track.unresolved_segments
    assert not track.verifier.residual_events
    assert not solve(cache, events, get_profile("broadcast")).cues
