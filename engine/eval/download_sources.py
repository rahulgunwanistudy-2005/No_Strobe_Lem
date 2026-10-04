"""Fetch and checksum the officially licensed evaluation films without playback."""

from nostrobe.config import Settings
from nostrobe.evaluation.manifest import fetch, read_manifest

if __name__ == "__main__":
    config = Settings()
    for source in read_manifest(config.eval_manifest).sources:
        print(fetch(source, config.eval_sources))
