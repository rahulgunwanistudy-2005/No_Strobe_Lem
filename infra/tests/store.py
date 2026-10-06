"""In-memory S3 adapter shared by cloud-free host and image checks."""

import hashlib
import io
from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError


def error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "S3")


class Store:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.metadata: dict[str, dict[str, str]] = {}
        self.uploads: list[str] = []
        self.conflict = False
        self.inject = None

    def get_object(self, **kw: Any) -> dict[str, Any]:
        key = kw["Key"]
        if key not in self.objects:
            raise error("NoSuchKey")
        payload = self.objects[key]
        etag = hashlib.md5(payload).hexdigest()
        match = kw.get("IfMatch")
        if match is not None and match.strip('"') != etag:
            raise error("PreconditionFailed")
        return {
            "Body": io.BytesIO(payload),
            "ContentLength": len(payload),
            "ETag": etag,
            "Metadata": self.metadata.get(key, {}),
        }

    def put_object(self, **kw: Any) -> None:
        key = kw["Key"]
        if key == "public/catalog.json" and self.inject:
            action, self.inject = self.inject, None
            action()
        current = self.objects.get(key)
        if (kw.get("IfNoneMatch") == "*" and current is not None) or (
            "IfMatch" in kw
            and (current is None or hashlib.md5(current).hexdigest() != kw["IfMatch"])
        ):
            self.conflict = True
            raise error("PreconditionFailed")
        self.objects[key] = kw["Body"]

    def upload_file(self, path: str, bucket: str, key: str, **kw: Any) -> None:
        self.uploads.append(key)
        self.objects[key] = Path(path).read_bytes()

    def get_paginator(self, name: str) -> "Store":
        return self

    def paginate(self, **kw: Any) -> list[dict[str, Any]]:
        # Multiple pages exercise pagination without a service or credentials.
        keys = sorted(k for k in self.objects if k.startswith(kw["Prefix"]))
        return [{"Contents": [{"Key": k} for k in keys[i : i + 2]]} for i in range(0, len(keys), 2)]
