"""S3 encoded smoke acceptance, preserving S1 truth and S2 profile expectations."""

import argparse
import json
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from nostrobe.analysis import analyze_cache
from nostrobe.config import Settings
from nostrobe.decode.cache import load_cache
from nostrobe.detect.pipeline import PROFILES
from nostrobe.domain.profiles import get_profile
from nostrobe.synth.generator import analytic_truth, encode, smoke_specs
from nostrobe.veil.composite import veil_timeline
from nostrobe.verify.verifier import detect_cached


def run(output: Path) -> None:
    started = time.perf_counter()
    rows = []
    for fps in (24, 25, 30, 50, 60):
        for original in smoke_specs():
            with tempfile.TemporaryDirectory(prefix="nostrobe-s3-suite-") as folder:
                root = Path(folder)
                spec = replace(original, fps=fps)
                path = root / f"HAZARD_{spec.name}.mp4"
                encode(path, spec)
                cache = load_cache(path, Settings(repo_root=root))
                params = [get_profile(p) for p in PROFILES]
                detected = detect_cached(cache, [], params)
                truth = analytic_truth(spec)
                for profile in PROFILES:
                    expected = truth.label == "must_fail"
                    if profile != "broadcast":
                        expected |= spec.name == "area_24"
                    if profile == "kids":
                        expected |= spec.name in ("rate_3", "isolated_3")
                    assert any(e.severity == "fail" for e in detected[profile]) == expected
                tracks = analyze_cache(cache, params)
                for track in tracks:
                    eligible = [
                        e
                        for e in track.events
                        if e.severity == "fail" or get_profile(track.profile).veil_warn
                    ]
                    assert track.verifier.passes or track.unresolved_segments
                    assert track.verifier.offsets_checked_s == [-0.15, 0.0, 0.15]
                    if not eligible:
                        assert not track.veils
                    if track.profile == "broadcast" and truth.label == "must_pass":
                        assert not track.veils
                    for t in cache.timestamps:
                        support = any(
                            c.t_on - c.ramp_in_s < t < c.t_off + c.ramp_out_s for c in track.veils
                        )
                        if not support:
                            assert veil_timeline(track.veils, float(t))[0] == 0
                    rows.append(
                        {
                            "name": spec.name,
                            "fps": fps,
                            "profile": track.profile,
                            "broadcast_truth": truth.label,
                            "passes": track.verifier.passes,
                            "unresolved": [u.model_dump() for u in track.unresolved_segments],
                            "n_veils": len(track.veils),
                            "stats": track.stats.model_dump(mode="json"),
                        }
                    )
            print(
                json.dumps({"completed": len(rows), "fps": fps, "clip": original.name}), flush=True
            )
            output.write_text(
                json.dumps(
                    {"elapsed_s": time.perf_counter() - started, "rows": rows},
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
