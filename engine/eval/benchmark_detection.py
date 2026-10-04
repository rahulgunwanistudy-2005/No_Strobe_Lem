"""Reproducible S2 timing; no playback, certification, or clean-control assertion."""

import argparse
import json
import platform
import resource
import subprocess
import time
from contextlib import closing
from pathlib import Path

from nostrobe.config import Settings
from nostrobe.decode.ffmpeg import probe
from nostrobe.detect.pipeline import PROFILES, DetectionPipeline, _cell_frames
from nostrobe.domain.profiles import get_profile


def benchmark(path: Path) -> dict[str, object]:
    config = Settings()
    media = probe(path, settings=config)
    pipeline = DetectionPipeline((90, 160), [get_profile(p) for p in PROFILES])
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    frames = 0
    detector_wall = detector_cpu = conversion_wall = 0.0
    start = time.perf_counter()
    cpu_start = time.process_time()
    previous = start
    with closing(_cell_frames(path, config)) as decoded:
        for luminance, rgb, t in decoded:
            ready = time.perf_counter()
            conversion_wall += ready - previous
            cpu = time.process_time()
            pipeline.update(luminance, rgb, t)
            detector_cpu += time.process_time() - cpu
            done = time.perf_counter()
            detector_wall += done - ready
            previous = done
            frames += 1
    events = pipeline.finish(media.duration_s)
    elapsed = time.perf_counter() - start
    cpu_elapsed = time.process_time() - cpu_start
    child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    result: dict[str, object] = {
        "media": media.model_dump(mode="json"),
        "frames": frames,
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "cpu": subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
            ).strip(),
            "ram_bytes": int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)),
        },
        "ffmpeg": subprocess.check_output([config.ffmpeg, "-version"], text=True).splitlines()[0],
        "decoder_threads": 1,
        "profiles": list(PROFILES),
        "wall_s": elapsed,
        "python_cpu_s": cpu_elapsed,
        "ffmpeg_cpu_s": child_after.ru_utime
        + child_after.ru_stime
        - child_before.ru_utime
        - child_before.ru_stime,
        "detector_wall_s": detector_wall,
        "detector_cpu_s": detector_cpu,
        "decode_and_cells_wall_s": conversion_wall,
        "end_to_end_x_realtime": media.duration_s / elapsed,
        "detector_wall_x_realtime": media.duration_s / detector_wall,
        "detector_cpu_x_realtime": media.duration_s / detector_cpu,
        "speed_target": 20,
        "speed_target_met": media.duration_s / detector_wall >= 20,
        "events": {p: [e.model_dump(mode="json") for e in items] for p, items in events.items()},
        "notes": (
            "All profiles in one decoding pass. Film flags are unreviewed detections; "
            "no clean-control accuracy claim."
        ),
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    measurement = benchmark(args.video)
    args.output.write_text(json.dumps(measurement, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps({k: v for k, v in measurement.items() if k not in ("events", "media")}, indent=2)
    )
