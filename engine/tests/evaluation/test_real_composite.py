import numpy as np

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import iter_analysis, probe
from nostrobe.synth.composite_real import encode_rgb


def test_encoded_composite_preserves_explicit_tags_and_rgb(tmp_path):
    frame = np.full((360, 640, 3), (60, 120, 180), dtype=np.uint8)
    path = tmp_path / "HAZARD_composite.mp4"
    config = Settings()
    encode_rgb(path, [frame] * 3, 25, config)
    media = probe(path, settings=config, require_bt709=True)
    assert media.fps == 25
    frames = list(iter_analysis(path, settings=config))
    assert len(frames) == 3
    for _, rgb, _ in frames:
        assert np.max(np.abs(rgb.astype(float) - frame)) <= 3
