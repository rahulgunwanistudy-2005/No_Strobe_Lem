"""Lossless compressed decoded-sample caches, bound to source and decode version."""

import json
from pathlib import Path

import numpy as np

from nostrobe.config import Settings
from nostrobe.decode.cache import CACHE_VERSION, FrameCache, load_cache
from nostrobe.evaluation.manifest import digest


def decoded(path: Path, directory: Path, config: Settings, stored: Path) -> FrameCache:
    source_hash = digest(path)
    archive = stored / f"{source_hash}-{CACHE_VERSION}.npz"
    cache_config = config.model_copy(update={"repo_root": directory})
    target = cache_config.cache_dir / f"{source_hash}-{CACHE_VERSION}"
    if archive.exists():
        target.mkdir(parents=True, exist_ok=True)
        with np.load(archive, allow_pickle=False) as data:
            manifest = str(data["manifest"].item())
            metadata = json.loads(manifest)
            if metadata["media"]["source_sha256"] != source_hash:
                raise ValueError("decoded cache checksum binding mismatch")
            (target / "manifest.json").write_text(manifest)
            np.save(target / "timestamps.npy", data["timestamps"], allow_pickle=False)
            for name, _ in metadata["shards"]:
                np.save(target / name, data[name], allow_pickle=False)
    cache = load_cache(path, cache_config)
    if not archive.exists():
        stored.mkdir(parents=True, exist_ok=True)
        arrays = {
            name: np.load(cache.directory / name, mmap_mode="r", allow_pickle=False)
            for name, _ in cache.shards
        }
        arrays["timestamps"] = cache.timestamps
        arrays["manifest"] = np.array((cache.directory / "manifest.json").read_text())
        temporary = archive.with_suffix(".tmp.npz")
        np.savez_compressed(temporary, **arrays)
        temporary.replace(archive)
    return cache
