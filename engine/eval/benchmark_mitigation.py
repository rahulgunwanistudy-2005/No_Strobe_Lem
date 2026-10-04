"""Time the complete CLI pipeline on a film; no raw media playback."""

import argparse
import json
import platform
import time
from pathlib import Path

from nostrobe.analysis import analyze
from nostrobe.config import Settings
from nostrobe.decode.cache import CACHE_VERSION
from nostrobe.decode.ffmpeg import probe
from nostrobe.domain.profiles import get_profile


def run(video: Path, output: Path, measurement: Path, profile: str) -> None:
    start = time.perf_counter()
    media = probe(video)
    cache_warm = (Settings().cache_dir / f"{media.source_sha256}-{CACHE_VERSION}").is_dir()
    tracks = analyze(video, output, [get_profile(profile)])
    elapsed = time.perf_counter() - start
    measurement.write_text(
        json.dumps(
            {
                "wall_s": elapsed,
                "decode_cache": "warm" if cache_warm else "cold",
                "x_realtime": media.duration_s / elapsed,
                "platform": platform.platform(),
                "python": platform.python_version(),
                "profile": profile,
                "media": media.model_dump(mode="json"),
                "tracks": [
                    {
                        "passes": t.verifier.passes,
                        "verifier": t.verifier.model_dump(mode="json"),
                        "stats": t.stats.model_dump(mode="json"),
                        "events": [e.model_dump(mode="json") for e in t.events],
                        "veils": [v.model_dump(mode="json") for v in t.veils],
                        "unresolved": [u.model_dump() for u in t.unresolved_segments],
                    }
                    for t in tracks
                ],
                "notes": (
                    "Full solve/final verification/report pipeline; "
                    "raw film flags remain unreviewed."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "wall_s": elapsed,
                "decode_cache": "warm" if cache_warm else "cold",
                "passes": [t.verifier.passes for t in tracks],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--measurement", type=Path, required=True)
    parser.add_argument("--profile", default="broadcast")
    args = parser.parse_args()
    run(args.video, args.out, args.measurement, args.profile)
