"""Live upload, catalog/source binding and public-prefix permission probe."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

import boto3
from nostrobe.track.jsonio import parse


def http_status(url: str) -> int:
    try:
        with urlopen(url, timeout=30) as response:
            return int(response.status)
    except HTTPError as exc:
        return exc.code


def run(
    bucket: str, region: str, source: Path, attribution: Path, timeout: int
) -> dict[str, object]:
    metadata = json.loads(attribution.read_text())
    required = {"credit", "license", "credit-url", "title"}
    if not required <= metadata.keys() or any(not isinstance(v, str) for v in metadata.values()):
        raise ValueError("attribution must supply credit, license, credit-url and title text")
    s3 = boto3.client("s3", region_name=region)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    key = "ingest/" + source.name
    started = time.monotonic()
    s3.upload_file(
        str(source), bucket, key, ExtraArgs={"ContentType": "video/mp4", "Metadata": metadata}
    )
    base = f"https://{bucket}.s3.{region}.amazonaws.com"
    while time.monotonic() - started < timeout:
        try:
            with urlopen(f"{base}/public/catalog.json", timeout=30) as response:
                catalog = json.load(response)
        except HTTPError as exc:
            if exc.code != 404:
                raise
            catalog = {"items": []}
        matched = [item for item in catalog["items"] if item["source_sha256"] == digest]
        if matched:
            item = matched[0]
            if set(item["tracks"]) != {"broadcast", "local", "kids"}:
                raise ValueError("catalog lacks all three profiles")
            for profile, entry in item["tracks"].items():
                with urlopen(entry["url"], timeout=30) as response:
                    track = parse(response.read().decode())
                if track.profile != profile or track.media.source_sha256 != digest:
                    raise ValueError("published track is not bound to the uploaded source")
            ingest_status = http_status(f"{base}/{quote(key)}")
            public_status = http_status(item["video"])
            if ingest_status != 403 or public_status != 200:
                raise ValueError(
                    f"permission gate failed: ingest={ingest_status}, public={public_status}"
                )
            return {
                "content_id": item["content_id"],
                "source_sha256": digest,
                "catalog_updated_s": time.monotonic() - started,
                "ingest_http_status": ingest_status,
                "public_http_status": public_status,
                "verified_profiles": ["broadcast", "local", "kids"],
                "catalog_url": f"{base}/public/catalog.json",
                "lambda_cost_per_video_hour": None,
                "cost_status": "collect billed duration and current regional prices separately",
            }
        time.sleep(5)
    raise TimeoutError("verified catalog entry did not appear before the configured deadline")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--attribution", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path("s7-live-validation.json"))
    args = parser.parse_args()
    result = run(args.bucket, args.region, args.source, args.attribution, args.timeout)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
