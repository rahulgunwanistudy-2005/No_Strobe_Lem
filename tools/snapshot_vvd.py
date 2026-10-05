"""Capture a single actual rendered VVD frame for UI inspection, not calibration."""

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from capture_vvd import png_rgb


def snapshot(proto_dir: Path, discovery: Path, output: Path) -> None:
    import grpc

    info = dict(
        line.split("=", 1) for line in discovery.read_text().splitlines() if "=" in line
    )
    with tempfile.TemporaryDirectory(prefix="nostrobe-ui-proto-") as generated:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                "-I",
                str(proto_dir),
                "--python_out=" + generated,
                "--grpc_python_out=" + generated,
                str(proto_dir / "emulator_controller.proto"),
            ],
            check=True,
        )
        sys.path.insert(0, generated)
        pb = importlib.import_module("emulator_controller_pb2")
        api = importlib.import_module("emulator_controller_pb2_grpc")
        with grpc.insecure_channel("127.0.0.1:" + info["grpc.port"].strip()) as channel:
            sent = time.monotonic_ns()
            image = api.EmulatorControllerStub(channel).getScreenshot(
                pb.ImageFormat(format=pb.ImageFormat.RGB888, width=960, height=540),
                timeout=3,
                metadata=[("authorization", "Bearer " + info["grpc.token"].strip())],
            )
            received = time.monotonic_ns()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(png_rgb(image.image, 960, 540))
            output.with_suffix(".json").write_text(
                json.dumps(
                    {
                        "method": "SDK EmulatorController.getScreenshot; single UI snapshot, not calibration",
                        "timestamp_us": image.timestampUs,
                        "request_ns": sent,
                        "received_ns": received,
                        "width": 960,
                        "height": 540,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proto-dir", type=Path, required=True)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot(args.proto_dir, args.discovery, args.output)
