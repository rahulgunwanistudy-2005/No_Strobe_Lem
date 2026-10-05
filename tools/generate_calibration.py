"""Generate device-only stimuli; never creates passing or production tracks."""

import argparse
from pathlib import Path

from nostrobe.calibration.stimuli import generate
from nostrobe.config import Settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    args = parser.parse_args()
    generate(args.output, args.font, Settings())
