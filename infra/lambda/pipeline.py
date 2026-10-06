"""Verified publication and listing-based catalog with optimistic concurrency."""

import hashlib
import json
import logging
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote_plus

from botocore.exceptions import ClientError
from config import Config
from nostrobe.analysis import analyze_cache
from nostrobe.config import Settings
from nostrobe.decode.cache import load_cache
from nostrobe.decode.ffmpeg import probe
from nostrobe.detect.pipeline import PROFILES
from nostrobe.domain.profiles import get_profile
from nostrobe.errors import NostrobeError, VerifierFailedError
from nostrobe.report.html import render
from nostrobe.track import jsonio, webvtt

LOG = logging.getLogger("pipeline")


class InputLimitError(NostrobeError):
    """Input cannot fit this bounded Lambda execution."""


class SourceChangedError(NostrobeError):
    """The notification refers to an older object version."""


def emit(message: str, **fields: Any) -> None:
    LOG.info(json.dumps({"message": message, **fields}, sort_keys=True, allow_nan=False))


def read_json(s3: Any, bucket: str, key: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in {"NoSuchKey", "404"}:
            return None, None
        raise
    body = response["Body"]
    try:
        return json.loads(body.read()), response["ETag"]
    finally:
        body.close()


def put_json(s3: Any, bucket: str, key: str, value: dict[str, Any], **conditions: Any) -> None:
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=(json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode(),
        ContentType="application/json",
        CacheControl="no-cache",
        **conditions,
    )


def rebuild_catalog(s3: Any, config: Config) -> None:
    # Read only the index ETag before listing. Never merge old catalog contents.
    for _ in range(12):
        _, etag = read_json(s3, config.bucket, "public/catalog.json")
        items = []
        pages = s3.get_paginator("list_objects_v2").paginate(Bucket=config.bucket, Prefix="public/")
        for page in pages:
            for obj in page.get("Contents", []):
                if not re.fullmatch(r"public/[^/]+/status.json", obj["Key"]):
                    continue
                status, _ = read_json(s3, config.bucket, obj["Key"])
                if status and status.get("state") == "ready":
                    items.append(status["item"])
        items.sort(key=lambda item: item["content_id"])
        condition = {"IfMatch": etag} if etag else {"IfNoneMatch": "*"}
        try:
            put_json(
                s3,
                config.bucket,
                "public/catalog.json",
                {"version": 1, "items": items},
                **condition,
            )
            return
        except ClientError as exc:
            if exc.response["Error"]["Code"] not in {
                "PreconditionFailed",
                "ConditionalRequestConflict",
                "412",
                "409",
            }:
                raise
    raise RuntimeError("catalog contention exceeded retry budget")


def status_once(s3: Any, config: Config, content_id: str, status: dict[str, Any]) -> None:
    key = f"public/{content_id}/status.json"
    previous, etag = read_json(s3, config.bucket, key)
    if previous and previous.get("state") == "ready":
        return
    try:
        put_json(
            s3, config.bucket, key, status, **({"IfMatch": etag} if etag else {"IfNoneMatch": "*"})
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] not in {"PreconditionFailed", "412"}:
            raise
        winner, _ = read_json(s3, config.bucket, key)
        if not winner or winner.get("state") != "ready":
            raise


def publish(s3: Any, config: Config, key: str, event_etag: str | None) -> dict[str, Any]:
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="nostrobe-", dir="/tmp") as temporary:
        work = Path(temporary)
        source = work / "source.mp4"
        response = s3.get_object(
            Bucket=config.bucket, Key=key, **({"IfMatch": event_etag} if event_etag else {})
        )
        body = response["Body"]
        digest, size = hashlib.sha256(), 0
        try:
            if response["ContentLength"] > config.max_input_bytes:
                raise InputLimitError("encoded input exceeds configured byte limit")
            with source.open("wb") as output:
                while block := body.read(1024 * 1024):
                    size += len(block)
                    if size > config.max_input_bytes:
                        raise InputLimitError("encoded input exceeds configured byte limit")
                    digest.update(block)
                    output.write(block)
        finally:
            body.close()
        slug = re.sub(r"[^a-z0-9]+", "-", Path(key).stem.lower()).strip("-")[:60] or "video"
        content_id = f"{digest.hexdigest()[:12]}-{slug}"
        source = source.rename(work / f"{content_id}.mp4")
        prefix = f"public/{content_id}"
        previous, _ = read_json(s3, config.bucket, f"{prefix}/status.json")
        if previous and previous.get("state") == "ready":
            rebuild_catalog(s3, config)
            emit("duplicate", content_id=content_id)
            return previous
        try:
            settings = Settings(repo_root=work)
            media = probe(source, settings=settings, require_bt709=True)
            if media.duration_s > config.max_duration_s:
                raise InputLimitError("video exceeds configured duration limit")
            # Cache preserves 640x360 original Y/RGB samples, four bytes per pixel.
            projected = (int(media.duration_s * media.fps) + 2) * 640 * 360 * 4
            if projected + config.storage_reserve_bytes > shutil.disk_usage(work).free:
                raise InputLimitError("decoded cache would exceed temporary storage")
            cache = load_cache(source, settings)
            tracks = analyze_cache(cache, [get_profile(p) for p in PROFILES])
            if {t.profile for t in tracks} != set(PROFILES) or any(
                not t.verifier.passes or t.verifier.residual_events or t.unresolved_segments
                for t in tracks
            ):
                raise VerifierFailedError("all three profiles must verify before publication")
            report = work / "report.html"
            report.write_text(render(tracks, cache=cache))
            counts = {}
            for track in tracks:
                counts[track.profile] = track.stats.n_events_by_kind
                target = work / f"{track.profile}.hzt.json"
                jsonio.write(target, track)
                vtt = work / f"{track.profile}.hzt.vtt"
                vtt.write_text(webvtt.serialize(track))
                for file, mime in [(target, "application/json"), (vtt, "text/vtt")]:
                    s3.upload_file(
                        str(file),
                        config.bucket,
                        f"{prefix}/{file.name}",
                        ExtraArgs={"ContentType": mime},
                    )
            s3.upload_file(
                str(report),
                config.bucket,
                f"{prefix}/report.html",
                ExtraArgs={"ContentType": "text/html; charset=utf-8"},
            )
            s3.upload_file(
                str(source),
                config.bucket,
                f"{prefix}/video.mp4",
                ExtraArgs={"ContentType": "video/mp4"},
            )
            base = f"{config.public_base_url}/{content_id}"
            metadata = response.get("Metadata", {})
            status: dict[str, Any] = {
                "state": "ready",
                "content_id": content_id,
                "item": {
                    "content_id": content_id,
                    "source_sha256": digest.hexdigest(),
                    "title": metadata.get("title", slug.replace("-", " ")),
                    "duration_s": media.duration_s,
                    "video": f"{base}/video.mp4",
                    "report": f"{base}/report.html",
                    "tracks": {
                        t.profile: {
                            "url": f"{base}/{t.profile}.hzt.json",
                            "hazard_count": len(t.events),
                        }
                        for t in tracks
                    },
                    "attribution": {
                        "credit": metadata.get("credit", "Uploader supplied media"),
                        "license": metadata.get("license", "Unspecified; no reuse license granted"),
                        "url": metadata.get("credit-url", "https://example.invalid/unprovided"),
                        "changes": "Source unchanged; verified HazardTrack sidecars added",
                    },
                },
                "metrics": {
                    "duration_s": media.duration_s,
                    "elapsed_s": time.monotonic() - started,
                    "input_bytes": size,
                    "profile_event_counts": counts,
                    "verifier_passes": {t.profile: t.verifier.passes for t in tracks},
                },
            }
            status_once(s3, config, content_id, status)
        except NostrobeError as exc:
            status = {
                "state": "error",
                "content_id": content_id,
                "error": {
                    "type": type(exc).__name__,
                    "message": "Input rejected; no catalog entry published",
                },
            }
            status_once(s3, config, content_id, status)
            emit("rejected", content_id=content_id, error_type=type(exc).__name__)
        rebuild_catalog(s3, config)
        emit("completed", content_id=content_id, **status.get("metrics", {}), state=status["state"])
        return status


def process(event: dict[str, Any], s3: Any, config: Config) -> dict[str, Any]:
    outcomes = []
    for record in event.get("Records", []):
        if record.get("eventSource") != "aws:s3" or not record.get("eventName", "").startswith(
            "ObjectCreated:"
        ):
            continue
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        if bucket != config.bucket or not key.startswith("ingest/") or not key.endswith(".mp4"):
            continue
        try:
            outcomes.append(publish(s3, config, key, record["s3"]["object"].get("eTag")))
        except InputLimitError as exc:
            identity = json.dumps(
                {"bucket": bucket, "key": key, "etag": record["s3"]["object"].get("eTag")},
                sort_keys=True,
            )
            rejected_id = "rejected-" + hashlib.sha256(identity.encode()).hexdigest()[:12]
            status = {
                "state": "error",
                "content_id": rejected_id,
                "source_binding": "notification-only; full source hash unavailable",
                "error": {"type": type(exc).__name__, "message": "Input exceeds byte limit"},
            }
            status_once(s3, config, rejected_id, status)
            emit("rejected", content_id=rejected_id, error_type=type(exc).__name__)
            rebuild_catalog(s3, config)
            outcomes.append(status)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in {"PreconditionFailed", "NoSuchKey", "412"}:
                emit("stale_notification", error_type=SourceChangedError.__name__)
                continue
            raise
    return {"results": outcomes}
