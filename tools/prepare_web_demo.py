"""Create an actually verified, nonhazardous overlay demonstration."""

import argparse
import json
import subprocess
from pathlib import Path

from nostrobe.analysis import analyze_cache
from nostrobe.config import Settings
from nostrobe.decode.cache import load_cache
from nostrobe.domain.models import VeilCue
from nostrobe.domain.profiles import get_profile
from nostrobe.track import jsonio, webvtt
from nostrobe.track.stats import track_stats
from nostrobe.verify.verifier import verify


def prepare(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    source = destination / "HAZARD_overlay-demo.mp4"
    (destination / "README.md").write_text(
        "# Synthetic media — do not autoplay\n\n"
        "This fixture uses constant gray, with deliberately added test veils. "
        "It demonstrates overlay timing, not hazardous-content detection or minimal mitigation.\n"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=gray:s=640x360:r=25:d=10",
            "-c:v",
            "libx264",
            "-x264-params",
            "colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off",
            "-pix_fmt",
            "yuv420p",
            "-color_range",
            "tv",
            "-colorspace",
            "bt709",
            str(source),
        ],
        check=True,
    )
    cache = load_cache(source, Settings(repo_root=destination))
    params = get_profile("broadcast")
    base = analyze_cache(cache, [params])[0]
    if base.events:
        raise ValueError("nonhazardous fixture unexpectedly contains events")
    cues = [
        VeilCue(
            id="demo",
            t_on=2,
            t_off=6,
            ramp_in_s=0.5,
            ramp_out_s=0.5,
            alpha=0.6,
            gray=0.25,
            covers=[],
        )
    ]
    result = verify(cache, cues, params)
    if not result.passes:
        raise ValueError("demonstration overlay does not verify")
    track = base.model_copy(
        update={
            "veils": cues,
            "verifier": result,
            "stats": track_stats([], cues, cache.media.duration_s),
        }
    )
    jsonio.write(destination / "broadcast.hzt.json", track)
    (destination / "broadcast.hzt.vtt").write_text(webvtt.serialize(track))
    (destination / "evidence.json").write_text(
        json.dumps(
            {
                "purpose": "nonhazardous browser overlay fixture; deliberate nonminimal veil",
                "source_sha256": cache.media.source_sha256,
                "input_events": len(base.events),
                "output_passes": result.passes,
                "offsets_checked_s": result.offsets_checked_s,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    prepare(parser.parse_args().destination)
