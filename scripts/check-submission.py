"""Check public copy, evidence bindings and local links before submission."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY = ["README.md", "tv/README.md", "docs/DEVPOST.md", "docs/JUDGE_QA.md"]
FORBIDDEN = re.compile(
    r"seizure-proof|prevents seizures|medically safe|\bcertified\b|Harding-compliant", re.I
)


def check() -> None:
    errors = []
    files = [ROOT / name for name in COPY]
    files.extend((ROOT / "tv/src").rglob("*.ts"))
    files.extend((ROOT / "tv/src").rglob("*.tsx"))
    for path in files:
        text = path.read_text()
        if FORBIDDEN.search(text):
            errors.append(f"Forbidden public copy: {path.relative_to(ROOT)}")
        if path.suffix == ".md":
            for target in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                local = target.split("#")[0]
                if not (path.parent / local).exists():
                    errors.append(f"Missing link: {path.relative_to(ROOT)} -> {local}")
    metrics_file = ROOT / "docs/evidence/s8/submission-metrics.json"
    metrics = json.loads(metrics_file.read_text())
    for key, name in [("results_sha256", "results.json"), ("report_sha256", "RESULTS.md")]:
        actual = hashlib.sha256((ROOT / "engine/eval" / name).read_bytes()).hexdigest()
        if metrics[key] != actual:
            errors.append(f"Stale submission metric binding: {name}")
    blocks = []
    for name in ("README.md", "docs/DEVPOST.md", "docs/JUDGE_QA.md"):
        text = (ROOT / name).read_text()
        block = text.split("<!-- submission-results:start -->", 1)[1].split(
            "<!-- submission-results:end -->", 1
        )[0]
        blocks.append(block.replace("../engine/", "engine/"))
    if len(set(blocks)) != 1:
        errors.append("Submission result tables differ")
    friction = (ROOT / "docs/FRICTION_LOG.md").read_text()
    ids = re.findall(r"^### (FL-\d+) ", friction, re.M)
    if len(ids) < 8 or len(set(ids)) != len(ids):
        errors.append("Friction entries must be distinct and evidence-backed")
    for field in (
        "Product / tool",
        "Date / version",
        "Task attempted",
        "Steps taken",
        "Expected",
        "Actual",
        "Severity",
        "Workaround",
        "Suggestion",
    ):
        if friction.count(f"- {field}:") != len(ids):
            errors.append(f"Incomplete friction field: {field}")
    if errors:
        raise ValueError("\n".join(errors))
    print(f"Copy, links, result bindings and {len(ids)} distinct friction entries pass")


if __name__ == "__main__":
    check()
