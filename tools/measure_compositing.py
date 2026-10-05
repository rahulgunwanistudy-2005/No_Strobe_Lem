"""Fit actual recorded device display codes against the specified overlay model."""

import argparse
import json
from pathlib import Path

from nostrobe.calibration.measure import compositing_measurement, read_capture
from nostrobe.config import Settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recording", type=Path, required=True)
    parser.add_argument("--descriptor", type=Path, required=True)
    parser.add_argument("--crop", help="w:h:x:y rectangle (ffmpeg crop order) of the video surface")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compositing_measurement(
        read_capture(args.recording, args.crop, Settings()),
        json.loads(args.descriptor.read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
