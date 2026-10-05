"""Measure a real >=60 fps device recording; never substitutes synthetic results."""

import argparse
import json
from pathlib import Path

from nostrobe.calibration.measure import combine_sync, read_capture, sync_measurement
from nostrobe.config import Settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recording", type=Path)
    parser.add_argument("--descriptor", type=Path)
    parser.add_argument("--scenario", choices=["steady", "seek", "pause_resume"])
    parser.add_argument(
        "--crop",
        help="w:h:x:y rectangle (ffmpeg crop order) of the video surface, excluding controls",
    )
    parser.add_argument("--combine", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.combine:
        result = combine_sync([json.loads(p.read_text()) for p in args.combine])
    else:
        if not (args.recording and args.descriptor and args.scenario):
            parser.error(
                "recording, descriptor and scenario are required unless combining runs"
            )
        result = sync_measurement(
            read_capture(args.recording, args.crop, Settings()),
            json.loads(args.descriptor.read_text()),
            args.scenario,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
