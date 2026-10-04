"""Publish only measured numbers, explicit denominators and unresolved reasons."""

from collections.abc import Sequence

from nostrobe.evaluation.metrics import Observation, summarize


def markdown(result: dict[str, object], rows: Sequence[Observation]) -> str:
    summary = summarize(rows)
    lines = [
        "# S4 evaluation results",
        "",
        f"Detection and verifier gate: **{'PASS' if result['gates_pass'] else 'NOT PASSED'}**.",
        "",
        "Headline numbers (these are the sole submission-number source):",
        "",
    ]
    for profile, value in summary.items():
        assert isinstance(value, dict)
        confusion = value["confusion"]
        assert isinstance(confusion, dict)
        lines.append(
            f"- {profile}: **{confusion['fn']} missed hazards** on "
            f"{confusion['tp'] + confusion['fn']} must-fail clips; "
            f"{confusion['fp']} false alarms on {confusion['tn'] + confusion['fp']} "
            "must-pass clips."
        )
    tracks = [r.track for r in rows if r.track is not None]
    lines += [
        f"- {sum(t.verifier.passes for t in tracks)}/{len(tracks)} profile tracks "
        "re-verify at −150, 0, +150 ms (default simulation tolerance; not device calibration).",
        f"- {sum(len(t.unresolved_segments) for t in tracks)} unresolved segments retained "
        "with reasons; publication refused for affected profile tracks.",
        "",
        "## Accuracy and interval overlap",
        "",
        "| Profile | TP | TN | FP | **FN** | IoU median | IoU p10 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for profile, value in summary.items():
        assert isinstance(value, dict)
        c = value["confusion"]
        assert isinstance(c, dict)
        med, p10 = value["iou_median"], value["iou_p10"]
        lines.append(
            f"| {profile} | {c['tp']} | {c['tn']} | {c['fp']} | **{c['fn']}** | {med} | {p10} |"
        )
    lines += ["", "| Suite | Profile | TP | TN | FP | FN |", "|---|---|---:|---:|---:|---:|"]
    for category in ("boundary", "shapes", "realistic"):
        for profile, value in summarize([r for r in rows if r.suite == category]).items():
            assert isinstance(value, dict)
            c = value["confusion"]
            assert isinstance(c, dict)
            lines.append(
                f"| {category} | {profile} | {c['tp']} | {c['tn']} | {c['fp']} | {c['fn']} |"
            )
    lines += [
        "",
        "## Viewing cost and verification",
        "",
        "Duration-weighted costs include simulated unresolved fallback veils; "
        "they do not imply those tracks can be published.",
        "",
        "| Profile | Verified / analyzed | Unresolved segments | Veiled runtime | "
        "Mean α during veil support | Mean ΔL cd/m² |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for profile, value in summary.items():
        assert isinstance(value, dict)
        lines.append(
            f"| {profile} | {value['verified_tracks']} / {value['analyzed_tracks']} | "
            f"{value['unresolved_segments']} | {value['veiled_fraction']:.6f} | "
            f"{value['mean_alpha']:.6f} | {value['mean_delta_cd_m2']:.6f} |"
        )
    lines += [
        "",
        "## Throughput",
        "",
        "All-profile shared passes. Full analyze includes "
        "cold decode/cache packing and detection/solve/verification; it excludes generation, "
        "truth calculation and report rendering. Detect includes cell conversion for the "
        "synthetic/composite cache runs. Full-film detect below measures detector updates "
        "separately. Host was not reserved for benchmarking.",
        "",
        "| Suite | Clips | Duration s | Detect × real-time | Full analyze × real-time |",
        "|---|---:|---:|---:|---:|",
    ]
    for suite in ("boundary", "shapes", "realistic", "clean"):
        group = [r for r in rows if r.suite == suite and r.profile == "broadcast"]
        if not group:
            continue
        duration = sum(r.duration_s for r in group)
        detect = sum(r.detect_s for r in group)
        full = sum(r.decode_s + (r.analyze_s or 0) for r in group)
        lines.append(
            f"| {suite} | {len(group)} | {duration:.6f} | "
            f"{duration / detect:.4f} | "
            + (f"{duration / full:.4f} |" if suite != "clean" else "not run (detection control) |")
        )
    lines += [
        "",
        "## Unmodified film controls",
        "",
        "The entire checksum-pinned films are decoded without modification. They have "
        "no independently reviewed interval truth and are excluded from confusion scores. "
        "Nonzero flags are **unreviewed**, neither confirmed true positives nor established "
        "false alarms. Traces show luminance only and never play raw footage. "
        "A whole-frame mean can hide local/red hazards; review the per-profile event evidence "
        "in results.json before claiming clean-film accuracy.",
        "",
        "| Film | Profile | Fail events | Warn events | Trace |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows:
        if row.suite == "clean":
            fails = sum(e.severity == "fail" for e in row.events)
            lines.append(
                f"| {row.name} | {row.profile} | {fails} | {len(row.events) - fails} | "
                f"[luminance trace]({row.trace}) |"
            )
    review = result.get("clean_context_review")
    if isinstance(review, dict):
        lines += ["", str(review["method"]), ""]
        for sample in review["broadcast_context"]:
            lines.append(f"- At {sample['sample_time_s']} s: {sample['context']}")
        lines += ["", str(review["conclusion"])]
    lines += ["", "## Unresolved and missed cases", ""]
    failures = []
    for row in rows:
        if row.truth and row.truth.must_fail and not any(e.severity == "fail" for e in row.events):
            failures.append(f"- **MISS** {row.suite}/{row.name}/{row.profile}")
        if row.track:
            for segment in row.track.unresolved_segments:
                failures.append(
                    f"- {row.suite}/{row.name}/{row.profile}: "
                    f"{segment.start:.6f}–{segment.end:.6f} s — {segment.reason}"
                )
    lines += failures or ["None."]
    lines += [
        "",
        "## Scope and reproducibility",
        "",
        "Boundary: all original smoke cases plus luminance regime, leading spacing, "
        "red chroma and quadrant/glitch cases at 24/25/30/50/60 fps. Shapes: seeded "
        "S1 primitive variations. Truth is calculated from raw pre-codec samples by an "
        "independent offline reversal/window oracle; codec/analysis mismatches remain "
        "visible in scores. Original S1 ground truth is unchanged. Local/Kids truth uses "
        "their own product policies. Exact red chromaticity threshold remains covered "
        "by numeric unit tests, because 8-bit encoding cannot represent arbitrary u′v′.",
        "",
        "Realistic: five effects over moving licensed footage at the manifest timestamps, "
        "90% effect / 10% source in display-code space. They test injected hazards against "
        "complex backgrounds; they are not a representative natural-content prevalence "
        "sample. Scene descriptors identify inspected reference frames, not scene-label truth.",
        "",
        str(result["timing_policy"]),
        "",
        "Decoded samples are compressed to bound disk use. Accuracy and timing observations "
        "are cached with source checksum and provenance. A repeated run regenerates "
        "byte-identical JSON and Markdown. generated_at in internal evaluation tracks "
        "is fixed to 2000-01-01 UTC; evaluation never publishes player tracks.",
        "",
        "## Environment",
        "",
        "```json",
    ]
    from nostrobe.evaluation.manifest import canonical

    lines += [
        canonical(result["environment"]).rstrip(),
        "```",
        "",
        "Provenance:",
        "",
        "```json",
        canonical(result["provenance"]).rstrip(),
        "```",
        "",
        "## Control exclusions and review",
        "",
        "Tears of Steel originals lack required BT.709 tags and are not clean controls. "
        "The zero-fail expectation on the retained control is reported honestly; independent "
        "review of its flags is outstanding, so the clean-control acceptance claim remains open.",
        "",
        "## PEAT cross-check",
        "",
        str(result["peat"]),
        "",
    ]
    return "\n".join(lines)
