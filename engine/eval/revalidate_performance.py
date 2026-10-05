"""Rerun S4 detection and every saved veil through the optimized full verifier.

Historical S4 results stay bound to their original code. This separate audit
checks exact event equality and fresh verification; it does not reuse outcomes
or claim fresh veil solving or new full-analyze timings.
"""

import argparse
import json
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from nostrobe.config import Settings
from nostrobe.decode.cache import CACHE_VERSION
from nostrobe.domain.profiles import get_profile
from nostrobe.evaluation.cache import decoded
from nostrobe.evaluation.manifest import canonical, digest
from nostrobe.evaluation.metrics import Observation, summarize
from nostrobe.evaluation.runner import code_hash, environment
from nostrobe.verify.verifier import detect_cached, verify

# Decoded archives contain original byte samples. These modules determine those
# bytes, source stimuli, truth and profile settings and must be unchanged.
INPUT_MODULES = (
    "decode/ffmpeg.py",
    "decode/cache.py",
    "decode/process.py",
    "synth/generator.py",
    "synth/composite_real.py",
    "evaluation/truth.py",
    "evaluation/suites.py",
    "domain/profiles.py",
    "luminance/bt1702_sdr_curve.csv",
)


def revalidate(baseline: Path, stored: Path, output: Path) -> None:
    config = Settings()
    old = json.loads(baseline.read_text())
    old_git = old["environment"]["git_sha"]
    for module in INPUT_MODULES:
        relative = f"engine/src/nostrobe/{module}"
        before = subprocess.check_output(
            ["git", "show", f"{old_git}:{relative}"], cwd=config.repo_root
        )
        if before != (config.repo_root / relative).read_bytes():
            raise ValueError(f"input-cache producer changed: {module}")
    jobs = defaultdict(list)
    for value in old["observations"]:
        row = Observation.model_validate(value)
        if row.truth is not None:
            jobs[(row.suite, row.name)].append(row)
    if len(jobs) != 325 or sum(map(len, jobs.values())) != 975:
        raise ValueError("expected the complete S4 synthetic/composite baseline")
    validated = []
    audit = []
    started = time.perf_counter()
    for (suite, name), rows in sorted(jobs.items()):
        path = config.synth_dir / f"s4/clips/HAZARD_{suite}_{name}.mp4"
        source_hash = digest(path)
        if any(row.source_sha256 != source_hash for row in rows):
            raise ValueError(f"source checksum changed: {suite}/{name}")
        archive = stored / f"{source_hash}-{CACHE_VERSION}.npz"
        if not archive.is_file():
            raise ValueError(f"missing original decoded samples: {archive.name}")
        with tempfile.TemporaryDirectory(prefix="nostrobe-performance-") as directory:
            cache = decoded(path, Path(directory), config, stored)
            events = detect_cached(cache, [], [get_profile(row.profile) for row in rows])
            for row in rows:
                if events[row.profile] != row.events:
                    raise ValueError(f"event output changed: {suite}/{name}/{row.profile}")
                if row.track is None:
                    raise ValueError("baseline track is missing")
                result = verify(
                    cache,
                    row.track.veils,
                    row.profile,
                    offsets=row.track.verifier.offsets_checked_s,
                )
                if not result.passes or result.residual_events:
                    raise ValueError(f"saved veil no longer verifies: {suite}/{name}/{row.profile}")
                validated.append(
                    row.model_copy(
                        update={
                            "events": events[row.profile],
                            "track": row.track.model_copy(update={"verifier": result}),
                        }
                    )
                )
                audit.append(
                    {
                        "suite": suite,
                        "name": name,
                        "profile": row.profile,
                        "source_sha256": source_hash,
                        "events_identical": True,
                        "veils": len(row.track.veils),
                        "verifier": result.model_dump(mode="json"),
                    }
                )
        print(f"revalidated {suite}/{name}: {len(validated)}/975", flush=True)
    result = {
        "format_version": "1.0",
        "baseline_sha256": digest(baseline),
        "baseline_provenance": old["provenance"],
        "code_sha256": code_hash(config),
        "environment": environment(config),
        "input_modules_unchanged": list(INPUT_MODULES),
        "decode_cache_version": CACHE_VERSION,
        "cases": len(jobs),
        "tracks": len(validated),
        "all_events_identical": True,
        "all_saved_veils_reverified": True,
        "wall_s": time.perf_counter() - started,
        "summary": summarize(validated),
        "observations": audit,
        "scope": "Fresh full-detector events and all saved-track offset verification. "
        "Original truth, stimuli, veils and costs retained; no fresh solver or analyze timings.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--decoded", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    revalidate(args.baseline, args.decoded, args.output)
