"""Actual encoded MP4 through the library and pipeline, without cloud credentials."""

import hashlib
import json
import subprocess
from pathlib import Path

from config import Config
from nostrobe.track.jsonio import parse
from nostrobe.track.webvtt import parse as parse_vtt
from pipeline import process
from test_pipeline import Store, event


def test_encoded_sdr_publishes_bound_verified_profiles(tmp_path: Path) -> None:
    source = tmp_path / "quiet.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=gray:s=640x360:r=25:d=1",
            "-c:v",
            "libx264",
            "-x264-params",
            "colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off",
            "-pix_fmt",
            "yuv420p",
            "-color_range",
            "tv",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
            str(source),
        ],
        check=True,
    )
    store = Store()
    store.objects["ingest/quiet.mp4"] = source.read_bytes()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    config = Config(bucket="media", public_base_url="https://media.example/public")
    outcome = process(event("ingest/quiet.mp4"), store, config)["results"][0]
    assert outcome["state"] == "ready"
    for profile in ("broadcast", "local", "kids"):
        prefix = f"public/{outcome['content_id']}/{profile}"
        track = parse(store.objects[f"{prefix}.hzt.json"].decode())
        assert track.verifier.passes and not track.events
        assert track.media.source_sha256 == digest
        assert track.media.content_id == outcome["content_id"]
        assert parse_vtt(store.objects[f"{prefix}.hzt.vtt"].decode()) == track
    assert len(json.loads(store.objects["public/catalog.json"])["items"]) == 1
