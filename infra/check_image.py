"""Verify the actual image's source binding, three-profile publication and size."""

import argparse
import json
import subprocess
from pathlib import Path


def check(image: str, source: Path, output: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    inspected = json.loads(
        subprocess.check_output(["docker", "image", "inspect", image], text=True)
    )[0]
    size = int(inspected["Size"])
    image_id = str(inspected["Id"])
    if size >= 1_000_000_000:
        raise ValueError(f"image exceeds 1 GB: {size} bytes")
    script = """
import json,hashlib,sys
from pathlib import Path
sys.path.insert(0, "/checks/infra/tests")
from config import Config
from pipeline import process
from store import Store
from nostrobe.track.jsonio import parse
from nostrobe.track.webvtt import parse as vtt
from nostrobe.config import Settings
store=Store()
payload=Path("/sample.mp4").read_bytes()
store.objects["ingest/sample.mp4"]=payload
event={"Records":[{"eventSource":"aws:s3","eventName":"ObjectCreated:Put",
"s3":{"bucket":{"name":"media"},"object":{"key":"ingest/sample.mp4"}}}]}
outcome=process(event,store,Config("media","https://example.com/public"))["results"][0]
assert outcome["state"] == "ready", outcome
for profile in ("broadcast","local","kids"):
    prefix="public/"+outcome["content_id"]+"/"+profile
    track=parse(store.objects[prefix+".hzt.json"].decode())
    assert track.verifier.passes
    assert track.media.source_sha256 == hashlib.sha256(payload).hexdigest()
    assert vtt(store.objects[prefix+".hzt.vtt"].decode()) == track
assert Path("/var/task/nostrobe/py.typed").exists()
assert Settings().repo_root == Path.cwd()
print(json.dumps(outcome, sort_keys=True))
"""
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,size=1g",
            "--entrypoint",
            "python",
            "-v",
            f"{root / 'infra/tests'}:/checks/infra/tests:ro",
            "-v",
            f"{source.resolve()}:/sample.mp4:ro",
            image_id,
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError("container smoke failed: " + result.stderr[-5000:])
    status = json.loads(result.stdout.splitlines()[-1])
    data = {
        "image": image,
        "image_id": image_id,
        "image_size_bytes": size,
        "size_budget_bytes": 1_000_000_000,
        "image_budget_passes": True,
        "read_only_runtime_passes": True,
        "environment": "Docker linux/amd64 on Apple Silicon with in-memory S3; not Lambda",
        "status": status,
        "aws_measured": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="nostrobe-lambda:s7")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("docs/s7/container-validation.json"))
    args = parser.parse_args()
    check(args.image, args.source, args.output)
