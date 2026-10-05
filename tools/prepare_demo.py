"""Prepare a CC-BY excerpt and reverify a gentle illustrative overlay before playback."""

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from nostrobe.config import Settings
from nostrobe.decode.cache import load_cache
from nostrobe.decode.ffmpeg import probe
from nostrobe.domain.models import HazardTrack, VeilCue
from nostrobe.domain.profiles import get_profile
from nostrobe.track.jsonio import write
from nostrobe.track.stats import track_stats
from nostrobe.verify.verifier import detect_cached, verify


def prepare(source: Path, output: Path) -> None:
    config = Settings()
    manifest = json.loads(config.eval_manifest.read_text())
    expected = next(item for item in manifest["sources"] if item["id"] == "bbb")
    with source.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected["sha256"]:
            raise ValueError(
                "demo source must match the licensed Big Buck Bunny manifest checksum"
            )
    probe(source, settings=config)
    output.mkdir(parents=True, exist_ok=True)
    video = output / "demo.mp4"
    subprocess.run(
        [
            config.ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-t",
            "12",
            "-an",
            "-vf",
            "scale=640:360:flags=area",
            "-c:v",
            "libx264",
            "-crf",
            "10",
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
            "-x264-params",
            "colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off",
            "-threads",
            "1",
            "-filter_threads",
            "1",
            "-movflags",
            "+faststart",
            str(video),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    cache = load_cache(video, settings=config)
    params = [get_profile(p) for p in ("broadcast", "local", "kids")]
    events = detect_cached(cache, [], params)
    if any(event.severity == "fail" for values in events.values() for event in values):
        raise ValueError("demo excerpt has unmitigated failures; do not play it")
    cues = [
        VeilCue(
            id="illustrative_overlay",
            t_on=3,
            t_off=7,
            ramp_in_s=1,
            ramp_out_s=1,
            alpha=0.25,
            gray=0.25,
            covers=[],
        )
    ]
    verified = [verify(cache, cues, p) for p in params]
    if any(not result.passes for result in verified):
        raise ValueError("illustrative overlay failed the verifier; do not publish")
    for profile, result in zip(params, verified, strict=True):
        track = HazardTrack(
            format="hazardtrack",
            format_version="1.0",
            profile=profile.profile,
            media=cache.media,
            events=events[profile.profile],
            veils=cues,
            verifier=result,
            generated_at=datetime.now(UTC),
            stats=track_stats(events[profile.profile], cues, cache.media.duration_s),
        )
        write(output / f"demo.{profile.profile}.hzt.json", track)
        if profile.profile == "broadcast":
            write(output / "demo.hzt.json", track)
    subprocess.run(
        [
            config.ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-ss",
            "1",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-threads",
            "1",
            str(output / "demo.jpg"),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    (output / "catalog.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "content_id": cache.media.content_id,
                        "source_sha256": cache.media.source_sha256,
                        "title": "Big Buck Bunny · gentle veil demonstration",
                        "description": "12-second opening excerpt. Illustrative overlay; no source hazard is claimed.",
                        "duration_s": cache.media.duration_s,
                        "video": "/demo.mp4",
                        "poster": "/demo.jpg",
                        "tracks": {
                            p.profile: {
                                "url": f"/demo.{p.profile}.hzt.json",
                                "hazard_count": 0,
                            }
                            for p in params
                        },
                        "attribution": {
                            "credit": "Big Buck Bunny (2008), Blender Foundation / Peach team",
                            "license": "CC-BY-3.0",
                            "url": "https://peach.blender.org/about/",
                            "changes": "12-second excerpt, resized to 640×360, audio removed; illustrative viewing overlay.",
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (output / "demo.json").write_text(
        json.dumps(
            {
                "title": "Big Buck Bunny · gentle veil demonstration",
                "video": "/demo.mp4",
                "track": "/demo.hzt.json",
                "content_id": track.media.content_id,
                "source_sha256": track.media.source_sha256,
                "attribution": "Big Buck Bunny (2008), Blender Foundation / Peach team, CC-BY-3.0",
                "license_url": "https://peach.blender.org/about/",
                "scope": "12-second opening excerpt; all profiles checked with and without overlay. "
                "The overlay demonstrates playback; it does not represent a source hazard.",
            },
            indent=2,
        )
        + "\n"
    )
    shutil.rmtree(cache.directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source, args.output)
