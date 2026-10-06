"""Synchronize submission tables with a complete, provenance-matched evaluation."""

import hashlib
import json
from pathlib import Path

from nostrobe.config import Settings
from nostrobe.evaluation.runner import code_hash

ROOT = Path(__file__).resolve().parents[1]


def update() -> None:
    source = ROOT / "engine/eval/results.json"
    data = json.loads(source.read_text())
    if not data["complete"] or not data["gates_pass"]:
        raise ValueError("Submission requires a complete passing evaluation")
    if data["provenance"]["code_sha256"] != code_hash(Settings(repo_root=ROOT)):
        raise ValueError("Evaluation implementation provenance is stale")
    summary = data["summary"]
    total = sum(row["analyzed_tracks"] for row in summary.values())
    verified = sum(row["verified_tracks"] for row in summary.values())
    tolerance = data["environment"]["sync_tolerance_s"] * 1000
    lines = [
        "Copied from [RESULTS.md]({link}) and its machine-readable results; "
        "these are synthetic/composite corpus scores.",
        "",
        "| Profile | Missed / must-fail | False alarms / must-pass | Veiled runtime | Mean α |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("broadcast", "local", "kids"):
        row = summary[name]
        c = row["confusion"]
        lines.append(
            f"| {name} | {c['fn']} / {c['tp'] + c['fn']} | "
            f"{c['fp']} / {c['tn'] + c['fp']} | "
            f"{100 * row['veiled_fraction']:.4f}% | {row['mean_alpha']:.6f} |"
        )
    unresolved = sum(row["unresolved_segments"] for row in summary.values())
    lines.extend(
        [
            "",
            f"{verified}/{total} profile tracks re-verify at "
            f"−{tolerance:.3f}, 0, +{tolerance:.3f} ms; "
            f"{unresolved} unresolved segments.",
        ]
    )
    block = "\n".join(lines)
    for name in ("README.md", "docs/DEVPOST.md", "docs/JUDGE_QA.md"):
        target = ROOT / name
        text = target.read_text()
        start, end = "<!-- submission-results:start -->", "<!-- submission-results:end -->"
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        link = "engine/eval/RESULTS.md" if name == "README.md" else "../engine/eval/RESULTS.md"
        target.write_text(
            before + start + "\n" + block.replace("{link}", link) + "\n" + end + after
        )
    evidence = ROOT / "docs/evidence/s8/submission-metrics.json"
    evidence.write_text(
        json.dumps(
            {
                "results_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "report_sha256": hashlib.sha256(
                    (source.parent / "RESULTS.md").read_bytes()
                ).hexdigest(),
                "code_sha256": data["provenance"]["code_sha256"],
                "summary": summary,
                "offset_ms": tolerance,
                "scope": "synthetic and composite clips; natural-film control excluded",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    update()
