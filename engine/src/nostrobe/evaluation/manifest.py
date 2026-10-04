"""Strict evaluation configuration; JSON is a dependency-free YAML 1.2 subset."""

import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    title: str
    author: str
    license: str
    license_url: str
    url: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    archive_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    member: str | None = None

    @property
    def filename(self) -> str:
        return self.member or self.url.rsplit("/", 1)[-1]


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    source: str
    start_s: float = Field(ge=0)
    effect: str


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: str
    seed: int
    fps: list[int] = Field(min_length=1)
    shapes_count: int = Field(ge=0)
    sources: list[Source]
    realistic: list[Scenario]
    clean: list[str]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_manifest(path: Path) -> Manifest:
    manifest = Manifest.model_validate_json(path.read_text())
    ids = [source.id for source in manifest.sources]
    if len(set(ids)) != len(ids) or len(set(manifest.clean)) != len(manifest.clean):
        raise ValueError("duplicate source/control identifiers")
    if any(
        value not in ids for value in [*manifest.clean, *(s.source for s in manifest.realistic)]
    ):
        raise ValueError("unknown footage source")
    if any(fps not in (24, 25, 30, 50, 60) for fps in manifest.fps):
        raise ValueError("unsupported evaluation frame rate")
    return manifest


def fetch(source: Source, directory: Path) -> Path:
    """Download once, reject changed bytes, and extract only the pinned member."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / source.filename
    if path.exists():
        if digest(path) != source.sha256:
            raise ValueError(f"source checksum mismatch: {source.id}")
        return path
    temporary = directory / f"{source.id}.download"
    try:
        with (
            urllib.request.urlopen(source.url, timeout=60) as response,
            temporary.open("wb") as out,
        ):
            shutil.copyfileobj(response, out)
        if digest(temporary) != (source.archive_sha256 or source.sha256):
            raise ValueError(f"download checksum mismatch: {source.id}")
        if source.member:
            with zipfile.ZipFile(temporary) as archive, archive.open(source.member) as member:
                with path.open("wb") as out:
                    shutil.copyfileobj(member, out)
            if digest(path) != source.sha256:
                path.unlink()
                raise ValueError(f"extracted checksum mismatch: {source.id}")
        else:
            temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def canonical(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
