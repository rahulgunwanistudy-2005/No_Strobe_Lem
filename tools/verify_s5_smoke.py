"""Freshly solve and verify all 80 encoded S3 cases at current measured settings."""

import json
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from nostrobe.analysis import analyze_cache
from nostrobe.config import Settings
from nostrobe.domain.profiles import get_profile
from nostrobe.evaluation.cache import decoded
from nostrobe.evaluation.manifest import canonical, digest
from nostrobe.evaluation.runner import calibration_evidence, code_hash
from nostrobe.synth.generator import analytic_truth, encode, smoke_specs


def run() -> None:
    config = Settings()
    evidence = calibration_evidence(config)
    if evidence is None:
        raise ValueError("measured timing and compositing evidence is required")
    output = config.synth_dir / "s5/smoke"
    output.mkdir(parents=True, exist_ok=True)
    profiles = [get_profile(p) for p in ("broadcast", "local", "kids")]
    rows = []
    counts = {p.profile: {"tp": 0, "tn": 0, "fp": 0, "fn": 0} for p in profiles}
    started = time.perf_counter()
    for fps in (24, 25, 30, 50, 60):
        for base in smoke_specs():
            spec = replace(base, fps=fps)
            path = output / f"HAZARD_{fps}_{spec.name}.mp4"
            encode(path, spec, settings=config)
            truth = analytic_truth(spec)
            with tempfile.TemporaryDirectory(prefix="nostrobe-s5-smoke-") as folder:
                cache = decoded(path, Path(folder), config, output / "decoded")
                tracks = analyze_cache(cache, profiles)
                for track in tracks:
                    expected = truth.label == "must_fail"
                    if track.profile in ("local", "kids"):
                        expected |= spec.name == "area_24"
                    if track.profile == "kids":
                        expected |= spec.name in ("rate_3", "isolated_3")
                    detected = any(e.severity == "fail" for e in track.events)
                    label = (
                        ("tp" if detected else "fn")
                        if expected
                        else ("fp" if detected else "tn")
                    )
                    counts[track.profile][label] += 1
                    rows.append(
                        {
                            "case": spec.name,
                            "fps": fps,
                            "profile": track.profile,
                            "source_sha256": digest(path),
                            "expected_fail": expected,
                            "events": [e.model_dump(mode="json") for e in track.events],
                            "veils": [c.model_dump(mode="json") for c in track.veils],
                            "verifier": track.verifier.model_dump(mode="json"),
                            "unresolved_segments": [
                                u.model_dump(mode="json")
                                for u in track.unresolved_segments
                            ],
                        }
                    )
            print(
                json.dumps(
                    {
                        "event": "s5_smoke_case",
                        "case": spec.name,
                        "fps": fps,
                        "outcomes": len(rows),
                    }
                ),
                flush=True,
            )
    passes = (
        len(rows) == 240
        and all(c["fp"] == c["fn"] == 0 for c in counts.values())
        and all(r["verifier"]["passes"] and not r["unresolved_segments"] for r in rows)
        and all(
            not r["veils"]
            for r in rows
            if r["profile"] == "broadcast" and not r["expected_fail"]
        )
    )
    report = {
        "format_version": 1,
        "mode": "fresh encode/detect/solve/final whole-file verification; no saved track reuse",
        "code_sha256": code_hash(config),
        "device_calibration": evidence,
        "params_hash": {p.profile: p.params_hash() for p in profiles},
        "sync_tolerance_s": profiles[0].sync_tolerance_s,
        "cases": 80,
        "outcomes": len(rows),
        "confusion": counts,
        "gates_pass": passes,
        "wall_s": time.perf_counter() - started,
        "observations": rows,
    }
    (config.eval_output / "s5_smoke_verification.json").write_text(canonical(report))
    if not passes:
        raise ValueError("S3 smoke gates failed; preserve and investigate the report")


if __name__ == "__main__":
    run()
