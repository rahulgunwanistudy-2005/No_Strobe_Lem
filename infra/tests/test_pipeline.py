import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from config import Config
from nostrobe.domain.models import HazardTrack
from nostrobe.errors import UnsupportedMediaError
from pipeline import InputLimitError, process, rebuild_catalog
from store import Store, error

ROOT = Path(__file__).resolve().parents[2]


def event(key: str = "ingest/film+name.mp4", **extra: Any) -> dict[str, Any]:
    return {
        "Records": [
            {
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {"bucket": {"name": "media"}, "object": {"key": key, **extra}},
            }
        ]
    }


@pytest.fixture
def config() -> Config:
    return Config(bucket="media", public_base_url="https://media.s3.example/public")


@pytest.fixture
def store() -> Store:
    store = Store()
    store.objects["ingest/film name.mp4"] = b"source"
    store.metadata["ingest/film name.mp4"] = {
        "credit": "Blender Foundation",
        "license": "CC-BY-3.0",
        "credit-url": "https://peach.blender.org",
    }
    return store


def tracks(content_id: str, passed: bool = True) -> list[HazardTrack]:
    template = HazardTrack.model_validate_json(
        (ROOT / "spec/examples/contract.hzt.json").read_text()
    )
    media = template.media.model_copy(update={"content_id": content_id})
    verifier = template.verifier.model_copy(
        update={"passes": passed, "offsets_checked_s": [-0.268875, 0, 0.268875]}
    )
    return [
        template.model_copy(update={"media": media, "profile": p, "verifier": verifier})
        for p in ("broadcast", "local", "kids")
    ]


def test_three_profile_commit_and_idempotent_retry(store: Store, config: Config) -> None:
    content_id = hashlib.sha256(b"source").hexdigest()[:12] + "-film-name"
    artifacts = tracks(content_id)
    with (
        patch("pipeline.probe", return_value=artifacts[0].media),
        patch("pipeline.load_cache"),
        patch("pipeline.analyze_cache", return_value=artifacts) as analyze,
        patch("pipeline.render", return_value="<html>traces</html>"),
    ):
        result = process(event(), store, config)["results"][0]
        assert result["state"] == "ready"
        assert result["content_id"] == content_id
        assert len(store.uploads) == 8
        catalog = json.loads(store.objects["public/catalog.json"])
        assert catalog["items"][0]["attribution"]["license"] == "CC-BY-3.0"
        assert len(catalog["items"][0]["tracks"]) == 3
        process(event(), store, config)
        assert analyze.call_count == 1
        assert len(store.uploads) == 8
        track = json.loads(store.objects[f"public/{content_id}/broadcast.hzt.json"])
        assert track["media"]["content_id"] == content_id


def test_unverified_profile_never_uploads_video_or_tracks(store: Store, config: Config) -> None:
    artifacts = tracks("fixture", False)
    with (
        patch("pipeline.probe", return_value=artifacts[0].media),
        patch("pipeline.load_cache"),
        patch("pipeline.analyze_cache", return_value=artifacts),
    ):
        result = process(event(), store, config)["results"][0]
    assert result["error"]["type"] == "VerifierFailedError"
    assert not store.uploads
    assert json.loads(store.objects["public/catalog.json"])["items"] == []


def test_hdr_rejection_has_typed_status(store: Store, config: Config) -> None:
    with patch("pipeline.probe", side_effect=UnsupportedMediaError("HDR")):
        result = process(event(), store, config)["results"][0]
    assert result["error"]["type"] == "UnsupportedMediaError"
    assert not store.uploads


def test_concurrent_catalog_writer_cannot_remove_an_item(config: Config) -> None:
    store = Store()
    store.objects["public/a/status.json"] = json.dumps(
        {"state": "ready", "item": {"content_id": "a"}}
    ).encode()
    rebuild_catalog(store, config)

    def concurrent() -> None:
        store.objects["public/b/status.json"] = json.dumps(
            {"state": "ready", "item": {"content_id": "b"}}
        ).encode()
        rebuild_catalog(store, config)

    store.inject = concurrent
    rebuild_catalog(store, config)
    assert store.conflict
    assert [i["content_id"] for i in json.loads(store.objects["public/catalog.json"])["items"]] == [
        "a",
        "b",
    ]


def test_stale_notifications_and_non_ingest_objects_are_ignored(
    store: Store, config: Config
) -> None:
    assert process(event(eTag="stale"), store, config) == {"results": []}
    assert process(event("public/video.mp4"), store, config) == {"results": []}


def test_transient_catalog_failure_propagates_for_lambda_retry(config: Config) -> None:
    with patch.object(Store, "get_object", side_effect=error("AccessDenied")):
        with pytest.raises(ClientError):
            rebuild_catalog(Store(), config)


def test_duration_and_disk_limits_refuse_before_analysis(store: Store, config: Config) -> None:
    media = tracks("fixture")[0].media.model_copy(update={"duration_s": 121})
    with patch("pipeline.probe", return_value=media), patch("pipeline.load_cache") as decode:
        result = process(event(), store, config)["results"][0]
        assert result["error"]["type"] == InputLimitError.__name__
        decode.assert_not_called()


def test_oversized_input_has_unbound_typed_status(store: Store) -> None:
    config = Config(bucket="media", public_base_url="https://example.com/public", max_input_bytes=2)
    outcome = process(event(), store, config)["results"][0]
    assert outcome["content_id"].startswith("rejected-")
    assert outcome["error"]["type"] == "InputLimitError"
    assert not store.uploads
    assert json.loads(store.objects["public/catalog.json"])["items"] == []


def test_matching_notification_etag_is_quoted_for_conditional_get(
    store: Store, config: Config
) -> None:
    digest = hashlib.md5(store.objects["ingest/film name.mp4"]).hexdigest()
    artifacts = tracks("fixture")
    with (
        patch("pipeline.probe", return_value=artifacts[0].media),
        patch("pipeline.load_cache"),
        patch("pipeline.analyze_cache", return_value=artifacts),
        patch("pipeline.render", return_value="<html>traces</html>"),
        patch.object(store, "get_object", wraps=store.get_object) as download,
    ):
        assert process(event(eTag=digest), store, config)["results"][0]["state"] == "ready"
        assert download.call_args_list[0].kwargs["IfMatch"] == f'"{digest}"'


def test_disk_preflight_refuses_before_decode(store: Store, config: Config) -> None:
    media = tracks("fixture")[0].media
    with (
        patch("pipeline.probe", return_value=media),
        patch("pipeline.shutil.disk_usage", return_value=type("Disk", (), {"free": 1})()),
        patch("pipeline.load_cache") as decode,
    ):
        result = process(event(), store, config)["results"][0]
    assert result["error"]["type"] == "InputLimitError"
    assert not store.uploads
    decode.assert_not_called()


def test_stream_limit_does_not_trust_content_length(store: Store) -> None:
    config = Config(bucket="media", public_base_url="https://example.com/public", max_input_bytes=2)
    original = store.get_object

    def underestimate(**kwargs: Any) -> dict[str, Any]:
        response = original(**kwargs)
        if kwargs["Key"].startswith("ingest/"):
            response["ContentLength"] = 1
        return response

    with patch.object(store, "get_object", side_effect=underestimate):
        result = process(event(), store, config)["results"][0]
    assert result["error"]["type"] == "InputLimitError"
    assert not store.uploads


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf")])
def test_misconfigured_duration_cannot_disable_input_limit(duration: float) -> None:
    with pytest.raises(ValueError):
        Config(
            bucket="media", public_base_url="https://example.com/public", max_duration_s=duration
        )
