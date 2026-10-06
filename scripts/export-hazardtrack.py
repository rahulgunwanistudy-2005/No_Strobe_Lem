"""Export the library and portable contracts, excluding product/device infrastructure."""

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(destination: Path) -> None:
    if destination.exists():
        raise ValueError("export destination must not already exist")
    destination.mkdir(parents=True)
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    for name in tracked:
        if name.startswith(("engine/", "spec/")) or name in {
            "LICENSE",
            ".gitignore",
            "scripts/test-web-reader.cjs",
            "docs/INTERPRETATIONS.md",
            "docs/SAFETY.md",
            "docs/ATTRIBUTION.md",
            "docs/SOURCES.json",
            "docs/BROWSER_VALIDATION.md",
            "docs/s7/web-fixture.json",
            "docs/s7/web-overlay.jpg",
            "docs/s7/web-overlay.mp4",
            "docs/s7/web-overlay-samples.json",
        }:
            if name == "engine/tests/calibration/test_capture_format.py":
                continue  # Host SDK acquisition test belongs to the product.
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
    # TypeScript generation is checked by the product; this repo owns schema drift.
    test = destination / "engine/tests/domain/test_models.py"
    text = test.read_text()
    start = text.index("def test_generated_types_do_not_drift()")
    end = text.index("def test_schema_cli", start)
    test.write_text(text[:start] + text[end:])
    for name in ("README.md", "CONTRIBUTING.md", ".github/workflows/ci.yml"):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "infra/oss" / name, target)
    (destination / "examples").mkdir()
    shutil.copytree(destination / "spec/examples/web", destination / "examples/web")
    shutil.copytree(destination / "spec/schema", destination / "schema")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    export(parser.parse_args().destination.resolve())
