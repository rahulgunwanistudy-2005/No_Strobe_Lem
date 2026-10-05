"""Record actual VVD rendered samples via the SDK's authenticated screenshot API.

Run with grpcio==1.76.0 and grpcio-tools==1.76.0. Acquisition is paced to leave the
emulator time to render; original SDK timestamps are never retimed, and frames
are never interpolated or duplicated.
"""

import argparse
import binascii
import importlib
import json
import queue
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from pathlib import Path
from typing import Any


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    )


def png_rgb(pixels: bytes, width: int, height: int) -> bytes:
    if width <= 0 or height <= 0 or len(pixels) != width * height * 3:
        raise ValueError("RGB sample dimensions do not match its bytes")
    stride = width * 3
    rows = b"".join(
        b"\0" + pixels[y * stride : (y + 1) * stride] for y in range(height)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(rows, 1))
        + png_chunk(b"IEND", b"")
    )


def record(
    proto_dir: Path,
    discovery: Path,
    output: Path,
    duration: float,
    width: int,
    max_fps: float = 110,
) -> None:
    import grpc

    info = dict(
        line.split("=", 1) for line in discovery.read_text().splitlines() if "=" in line
    )
    port = int(info["grpc.port"])
    # Existing local token is used only in memory. Never print or save it.
    metadata = [("authorization", "Bearer " + info["grpc.token"].strip())]
    output.mkdir(parents=True, exist_ok=False)
    height = width * 9 // 16
    with tempfile.TemporaryDirectory(prefix="nostrobe-vvd-proto-") as generated:
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
        with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
            stub = api.EmulatorControllerStub(channel)
            pending: queue.Queue[tuple[int, bytes] | None] = queue.Queue(maxsize=12)
            failures: list[Exception] = []

            def writer() -> None:
                while True:
                    item = pending.get()
                    try:
                        if item is None:
                            return
                        index, pixels = item
                        if not failures:
                            (output / f"{index:06}.png").write_bytes(
                                png_rgb(pixels, width, height)
                            )
                    except (OSError, ValueError, zlib.error) as exc:
                        failures.append(exc)
                    finally:
                        pending.task_done()

            worker = threading.Thread(target=writer)
            worker.start()
            samples: list[dict[str, Any]] = []
            start = time.monotonic()
            try:
                while time.monotonic() - start < duration:
                    sent = time.monotonic_ns()
                    image = stub.getScreenshot(
                        pb.ImageFormat(
                            format=pb.ImageFormat.RGB888, width=width, height=height
                        ),
                        timeout=3,
                        metadata=metadata,
                    )
                    received = time.monotonic_ns()
                    pixels = (
                        image.image
                    )  # Access once: protobuf copies the whole buffer.
                    if len(pixels) != width * height * 3:
                        raise ValueError("empty/inactive or wrong-size rendered frame")
                    if samples and image.timestampUs <= samples[-1]["timestamp_us"]:
                        raise ValueError(
                            "SDK capture timestamps must strictly increase"
                        )
                    samples.append(
                        {
                            "frame": len(samples),
                            "timestamp_us": image.timestampUs,
                            "request_ns": sent,
                            "received_ns": received,
                        }
                    )
                    pending.put((len(samples) - 1, pixels))
                    if failures:
                        raise failures[0]
                    # Pace acquisition to leave the emulator time to render.
                    # Actual SDK timestamps remain authoritative; no retiming.
                    remaining = 1 / max_fps - (time.monotonic_ns() - sent) / 1e9
                    if remaining > 0:
                        time.sleep(remaining)
            finally:
                pending.put(None)
                pending.join()
                worker.join()
            if failures:
                raise failures[0]
    if len(samples) < 2:
        raise ValueError("capture needs at least two real timestamped samples")
    fps = (len(samples) - 1) / (
        (samples[-1]["timestamp_us"] - samples[0]["timestamp_us"]) / 1e6
    )
    (output / "capture.json").write_text(
        json.dumps(
            {
                "method": "SDK EmulatorController.getScreenshot RGB888; live rendered surface",
                "timestamp_origin": "SDK frame estimate, Unix microseconds",
                "width": width,
                "height": height,
                "effective_fps": fps,
                "requested_max_fps": max_fps,
                "frames": samples,
            },
            indent=2,
        )
        + "\n"
    )
    with (output / "frames.ffconcat").open("w") as listing:
        listing.write("ffconcat version 1.0\n")
        for i, sample in enumerate(samples):
            listing.write(f"file '{i:06}.png'\noption framerate 1000000\n")
            if i + 1 < len(samples):
                delta = (samples[i + 1]["timestamp_us"] - sample["timestamp_us"]) / 1e6
                listing.write(f"duration {delta:.6f}\n")
    print(json.dumps({"event": "vvd_capture", "frames": len(samples), "fps": fps}))
    if fps < 59.9:
        raise ValueError("capture below 60 fps: reject it; do not retime it")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proto-dir", type=Path, required=True)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument(
        "--width", type=int, default=960, choices=[640, 960, 1280, 1920]
    )
    parser.add_argument("--max-fps", type=float, default=110)
    args = parser.parse_args()
    if not 0 < args.duration <= 120:
        parser.error("capture duration must be between 0 and 120 seconds")
    if not 60 <= args.max_fps <= 240:
        parser.error("maximum capture rate must be between 60 and 240 fps")
    record(
        args.proto_dir,
        args.discovery,
        args.output,
        args.duration,
        args.width,
        args.max_fps,
    )
