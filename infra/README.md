# Verified AWS ingest

See [AWS operations](../docs/AWS.md) for deploy, validation, costs and teardown.

```sh
uv sync --locked
uv run ruff check lambda tests smoke.py check_image.py
uv run ruff format --check lambda tests smoke.py check_image.py
uv run mypy --strict lambda smoke.py check_image.py
uv run pytest -q
```

The integration test encodes a quiet SDR MP4 and exercises the real engine;
S3 is an in-memory adapter. It is not a cloud benchmark. The public catalog's
schema matches `tv/src/catalog/api.ts`. Test notification replay and competing
catalog builders before changing publication order.

From the product repository root,
`uv run --directory infra python check_image.py --source INPUT.mp4`
checks an actual Docker image's <1 GB size, read-only execution, installed wheel
and three source-bound JSON/WebVTT tracks. See the operations guide for building
the `nostrobe-lambda:s7` image before running this check. All local results and
the still-open cloud gates are recorded in [the S7 report](../docs/S7_REPORT.md).
