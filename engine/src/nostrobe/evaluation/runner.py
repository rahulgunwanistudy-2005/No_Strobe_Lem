"""Provenance-bound evaluation, resumable evidence and deterministic reporting."""

import hashlib
import json
import logging
import platform
import shutil
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from matplotlib.figure import Figure

from nostrobe import __version__
from nostrobe.analysis import analyze_cache
from nostrobe.config import Settings
from nostrobe.decode.cache import FrameCache
from nostrobe.decode.ffmpeg import iter_analysis, probe, to_cells
from nostrobe.detect.pipeline import PROFILES, DetectionPipeline
from nostrobe.domain.profiles import get_profile
from nostrobe.evaluation.cache import decoded
from nostrobe.evaluation.manifest import canonical, digest, fetch, read_manifest
from nostrobe.evaluation.metrics import Observation, summarize
from nostrobe.evaluation.suites import boundary_specs, shape_specs
from nostrobe.evaluation.truth import ProfileTruth, oracle
from nostrobe.synth.composite_real import composite_frames, encode_rgb
from nostrobe.synth.generator import ClipSpec, encode, iter_frames
from nostrobe.verify.verifier import detect_cached

LOGGER = logging.getLogger("nostrobe")


def environment(config: Settings) -> dict[str, object]:
    version = subprocess.run(
        [config.ffmpeg, "-version"], capture_output=True, text=True, check=True
    )
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=config.repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    hardware = (
        subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        if (platform.system() == "Darwin")
        else None
    )
    cpu = (
        subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
        if platform.system() == "Darwin"
        else None
    )
    return {
        "cpu_model": cpu.stdout.strip() if cpu and cpu.returncode == 0 else platform.processor(),
        "engine_version": __version__,
        "ffmpeg": version.stdout.splitlines()[0],
        "git_sha": git.stdout.strip(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "memory_bytes": int(hardware.stdout) if hardware and hardware.returncode == 0 else None,
        "params_hash": {p: get_profile(p).params_hash() for p in PROFILES},
    }


def code_hash(config: Settings) -> str:
    root = Path(__file__).resolve().parents[1]
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        hasher.update(str(path.relative_to(root)).encode())
        hasher.update(path.read_bytes())
    hasher.update((root / "luminance/bt1702_sdr_curve.csv").read_bytes())
    hasher.update((config.repo_root / "engine/uv.lock").read_bytes())
    return hasher.hexdigest()


def _rows(
    cache: FrameCache, suite: str, name: str, truth: dict[str, ProfileTruth], decode_s: float
) -> list[Observation]:
    params = [get_profile(p) for p in PROFILES]
    started = time.perf_counter()
    detected = detect_cached(cache, [], params)
    detect_s = time.perf_counter() - started
    started = time.perf_counter()
    tracks = analyze_cache(cache, params)
    analyze_s = time.perf_counter() - started
    return [
        Observation(
            suite=suite,
            name=name,
            profile=t.profile,
            source_sha256=cache.media.source_sha256,
            duration_s=cache.media.duration_s,
            truth=truth[t.profile],
            events=detected[t.profile],
            track=t.model_copy(update={"generated_at": datetime(2000, 1, 1, tzinfo=UTC)}),
            detect_s=detect_s,
            analyze_s=analyze_s,
            decode_s=decode_s,
        )
        for t in tracks
    ]


def _clean(path: Path, name: str, config: Settings, output: Path) -> list[Observation]:
    """Stream full films once; keep every flag and a static whole-film trace.

    Clean controls test source detection, not mitigation, and have no assumed
    binary truth. This avoids scoring genuine flashes as algorithm false alarms.
    """
    import numpy as np

    from nostrobe.decode.ffmpeg import block_mean
    from nostrobe.luminance.color import rgb24_to_linear

    media = probe(path, settings=config, require_bt709=True)
    pipeline = DetectionPipeline((90, 160), [get_profile(p) for p in PROFILES])
    times, means = [], []
    detector_s = 0.0
    started = time.perf_counter()
    frames = iter_analysis(path, settings=config)
    try:
        for y, rgb, t in frames:
            luma = to_cells(y)
            color = block_mean(rgb24_to_linear(rgb))
            tick = time.perf_counter()
            pipeline.update(luma, color, t)
            detector_s += time.perf_counter() - tick
            times.append(t)
            means.append(float(luma.mean()))
    finally:
        frames.close()
    events = pipeline.finish(media.duration_s)
    full_s = time.perf_counter() - started
    output.mkdir(parents=True, exist_ok=True)
    figure = Figure(figsize=(12, 3), layout="constrained")
    axis = figure.subplots()
    axis.plot(times, means, linewidth=0.5)
    for event in events["broadcast"]:
        if event.severity == "fail":
            axis.axvspan(event.t_start, event.t_end, color="red", alpha=0.15)
    axis.set(xlabel="Media time (s)", ylabel="Mean luminance (cd/m²)", title=name)
    trace = f"traces/{name}.png"
    figure.savefig(output.parent / trace, backend="agg")
    # Keep numerical trace alongside flags for independent review without playback.
    np.savez_compressed(output / f"{name}.npz", time=times, mean_cd_m2=means)
    return [
        Observation(
            suite="clean",
            name=name,
            profile=p,
            source_sha256=media.source_sha256,
            duration_s=media.duration_s,
            truth=None,
            events=events[p],
            track=None,
            detect_s=detector_s,
            analyze_s=None,
            decode_s=full_s - detector_s,
            trace=trace,
        )
        for p in PROFILES
    ]


def run_eval(
    *,
    manifest_path: Path | None = None,
    output: Path | None = None,
    fresh_measurements: bool = False,
    resume: bool = False,
    suite: str = "all",
    settings: Settings | None = None,
) -> bool:
    config = settings or Settings()
    manifest_file = manifest_path or config.eval_manifest
    manifest = read_manifest(manifest_file)
    destination = output or config.eval_output
    if suite not in ("all", "boundary", "shapes", "realistic", "clean"):
        raise ValueError("unknown evaluation suite")
    destination.mkdir(parents=True, exist_ok=True)
    env = environment(config)
    review_file = config.eval_output / "control_review.json"
    review = json.loads(review_file.read_text()) if review_file.exists() else None
    provenance = {
        "code_sha256": code_hash(config),
        "manifest_sha256": digest(manifest_file),
        "control_review_sha256": digest(review_file) if review_file.exists() else None,
        "ffmpeg": env["ffmpeg"],
        "python": env["python"],
        "machine": env["machine"],
        "cpu_model": env.get("cpu_model"),
        "memory_bytes": env.get("memory_bytes"),
        "platform": env.get("platform"),
        "params_hash": env["params_hash"],
    }
    fingerprint = hashlib.sha256(canonical(provenance).encode()).hexdigest()
    evidence = config.synth_dir / "s4/evidence" / fingerprint
    evidence.mkdir(parents=True, exist_ok=True)
    env_file = evidence / "environment.json"
    if fresh_measurements or not env_file.exists():
        env_file.write_text(canonical(env))
    env = json.loads(env_file.read_text())
    rows: list[Observation] = []
    media_dir = config.synth_dir / "s4/clips"
    media_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[str, str, ClipSpec | None]] = []
    if suite in ("all", "boundary"):
        jobs.extend(("boundary", s.name, s) for s in boundary_specs(manifest.seed, manifest.fps))
    if suite in ("all", "shapes"):
        jobs.extend(
            ("shapes", s.name, s)
            for s in shape_specs(manifest.seed, manifest.shapes_count, manifest.fps)
        )
    if suite in ("all", "realistic"):
        jobs.extend(("realistic", s.name, None) for s in manifest.realistic)
    if suite in ("all", "clean"):
        jobs.extend(("clean", name, None) for name in manifest.clean)
    for category, name, spec in jobs:
        record = evidence / f"{category}_{name}.json"
        prior = (
            [Observation.model_validate(v) for v in json.loads(record.read_text())]
            if (record.exists() and not fresh_measurements)
            else []
        )
        if prior and resume:
            path = (
                config.eval_sources / next(s.filename for s in manifest.sources if s.id == name)
                if category == "clean"
                else media_dir / f"HAZARD_{category}_{name}.mp4"
            )
            if digest(path) != prior[0].source_sha256:
                raise ValueError(f"cached evidence source mismatch: {name}")
            observed = prior
            # Restore immutable trace evidence when reports are written elsewhere.
            if category == "clean":
                for suffix in ("png", "npz"):
                    target = destination / f"traces/{name}.{suffix}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(evidence / f"{name}.{suffix}", target)
        else:
            if category == "clean":
                source = next(s for s in manifest.sources if s.id == name)
                observed = _clean(
                    fetch(source, config.eval_sources), name, config, destination / "traces"
                )
                for suffix in ("png", "npz"):
                    shutil.copy2(
                        destination / f"traces/{name}.{suffix}", evidence / f"{name}.{suffix}"
                    )
            else:
                path = media_dir / f"HAZARD_{category}_{name}.mp4"
                truth_path = evidence / f"{category}_{name}.truth.json"
                if not truth_path.exists() or not path.exists():
                    if spec is not None:
                        truth = oracle(list(iter_frames(spec)), spec.fps)
                        encode(path, spec, settings=config)
                    else:
                        scenario = next(s for s in manifest.realistic if s.name == name)
                        source = next(s for s in manifest.sources if s.id == scenario.source)
                        frames = composite_frames(
                            fetch(source, config.eval_sources),
                            scenario.effect,
                            scenario.start_s,
                            25,
                            settings=config,
                        )
                        truth = oracle(frames, 25)
                        encode_rgb(path, frames, 25, config)
                    truth_path.write_text(
                        canonical(
                            {
                                "source_sha256": digest(path),
                                "profiles": {p: v.model_dump() for p, v in truth.items()},
                            }
                        )
                    )
                payload = json.loads(truth_path.read_text())
                if digest(path) != payload["source_sha256"]:
                    raise ValueError(f"generated clip checksum mismatch: {name}")
                truth = {p: ProfileTruth.model_validate(v) for p, v in payload["profiles"].items()}
                with tempfile.TemporaryDirectory(prefix="nostrobe-eval-") as folder:
                    started = time.perf_counter()
                    cache = decoded(path, Path(folder), config, evidence / "decoded")
                    decode_s = time.perf_counter() - started
                    observed = _rows(cache, category, name, truth, decode_s)
            if prior:
                for old, new in zip(prior, observed, strict=True):
                    if old.source_sha256 != new.source_sha256:
                        raise ValueError(f"cached measurement source mismatch: {name}")
                observed = [
                    new.model_copy(
                        update={
                            "detect_s": old.detect_s,
                            "analyze_s": old.analyze_s,
                            "decode_s": old.decode_s,
                        }
                    )
                    for old, new in zip(prior, observed, strict=True)
                ]
            record.write_text(canonical([r.model_dump(mode="json") for r in observed]))
        rows.extend(observed)
        LOGGER.info(
            "eval completed suite=%s clip=%s outcomes=%d/%d",
            category,
            name,
            len(rows),
            len(jobs) * 3,
        )
    summary = summarize(rows)
    complete = suite == "all" and bool(jobs)
    gates = complete and all(
        bool(v["gate_passes"]) for v in summary.values() if isinstance(v, dict)
    )
    result = {
        "format_version": "1.0",
        "seed": manifest.seed,
        "suite": suite,
        "complete": complete,
        "gates_pass": gates,
        "environment": env,
        "provenance": provenance,
        "summary": summary,
        "by_suite": {
            name: summarize([r for r in rows if r.suite == name])
            for name in ("boundary", "shapes", "realistic")
        },
        "unique_source_checksums": len({r.source_sha256 for r in rows}),
        "clean_context_review": review,
        "clean_adjudication_complete": False,
        "control_exclusions": [
            "Tears of Steel originals lack required BT.709 tags; not scored as clean controls"
        ],
        "observations": [r.model_dump(mode="json") for r in rows],
        "peat": "not run: no Windows PEAT environment available",
        "timing_policy": "First measured observations cached by code/manifest/tool/params hash; "
        "use --fresh-measurements to measure again. Accuracy is recomputed on every default run; "
        "--resume reuses matching completed evidence. Decoded samples are losslessly compressed "
        "and checksum-keyed; full films are streamed without mitigation.",
    }
    from nostrobe.evaluation.report import markdown

    (destination / "results.json").write_text(canonical(result))
    (destination / "RESULTS.md").write_text(markdown(result, rows))
    return gates
