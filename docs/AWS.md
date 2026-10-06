# AWS pipeline

The infrastructure analyzes explicitly tagged, limited-range, 8-bit SDR BT.709
MP4s. It publishes a title only when **all three profiles** pass whole-file
verification with no residual or unresolved events. The canonical content id is
`source_sha256[:12] + '-' + slugified_name`. Source files remain private under
`ingest/`; verified artifacts and typed statuses live under `public/`.

```
private S3 ingest/*.mp4
         |
         v  ObjectCreated (prefix + suffix filter)
Lambda Python 3.12 container [3008 MB / 900 s / 10 GiB / concurrency 2]
  stream download -> hash -> strict probe -> storage preflight
  decode once -> Broadcast / Local / Kids solve + verify
         |
         +-> rejected input: typed public/{id}/status.json, no catalog entry
         |
         v  all three pass
public/{id}/video.mp4 + {profile}.hzt.json + {profile}.hzt.vtt + report.html
         |
         v  commit ready status last
list public/*/status.json -> conditional ETag write -> public/catalog.json
         |
         v
TV catalog / portable HTML5 metadata reader
```

A catalog rebuild reads the old catalog's ETag, then derives every entry from
listing ready statuses. It never merges old catalog contents. Conditional
`If-Match` / `If-None-Match` writes detect overlapping builders; losers relist
and retry. This prevents an older listing from removing a concurrently published
item. [AWS conditional-write semantics](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)
are exercised in the deterministic concurrency regression. A duplicate event
repairs the catalog without repeating analysis. Notifications for overwritten
objects use an ETag download precondition and are ignored when stale.

The public status for a rejected oversized download uses a notification-derived
`rejected-*` id and explicitly states that a full source hash was unavailable.
Other rejected inputs use the source-bound id. Logs expose typed errors, content
id, video/processing duration, per-profile event counts and verifier outcomes;
they do not print event bodies, access credentials or source metadata. SDK
failures propagate so Lambda retries them. An interrupted invocation can leave
verified orphan artifacts, but a ready status is required for catalog discovery.
A hard Lambda timeout cannot write its own status; inspect CloudWatch/retries.

## Build and deploy

Install Docker, Python 3.12, uv, AWS CLI and AWS SAM CLI. Sign in using an AWS
profile with deploy privileges; the Lambda execution role itself only reads
`ingest/*`, reads/writes `public/*` and lists the `public/` prefix. SAM adds its
standard CloudWatch logging execution policy. Logs expire after seven days.

The final container uses a pinned Lambda base digest, a checksum-pinned minimal
static ffmpeg release bundle and the CI-built reference-library release wheel. Runtime
packages are version/hash pinned in `infra/runtime-requirements.txt`. The small
ffmpeg build includes MOV/MP4 demuxing, H.264/H.265 decoding, raw output and the
analysis filters; it excludes network protocols, capture and synthesis encoders.
ffmpeg is separately licensed under LGPL-2.1-or-later. Its source archive and
license are included in the image; the bundle includes its build recipe and provenance. `Dockerfile.source`
reproduces the source build; the normal Dockerfile downloads its tested binaries
to avoid slow compiler/bootstrap work in SAM's separate builder.

To exercise the actual image locally, from the repository root:

```sh
docker build --platform linux/amd64 -f infra/lambda/Dockerfile -t nostrobe-lambda:s7 .
uv run --directory infra python check_image.py --source ../synth_out/s7/ccby/bbb-opening.mp4 \
  --output ../docs/s7/container-validation.json
```

This uses a read-only root and in-memory S3 adapter, so it verifies packaging
and the real analysis path without establishing cloud performance or policy.

From the repository root, with an authenticated AWS profile/region:

```sh
sam build --template-file infra/template.yaml
sam deploy --guided --resolve-image-repos
```

Choose a globally unique lowercase `BucketName`. Keep reserved concurrency at
two and the default 120 s maximum duration. Inputs also have a 512 MiB encoded
limit and a decoded-cache disk preflight; high-fps inputs may be rejected below
the duration limit. A large cache or expensive solver can exceed the execution
budget; use short test clips while establishing real throughput. No claim is
made that arbitrary-length films finish inside Lambda's 15-minute limit.

The bucket blocks/ignores public ACLs and exposes only `public/*` via policy.
Account-level S3 Block Public Access can still prevent that policy; inspect your
test account's settings before deployment. Do not disable protection on unrelated
buckets. CORS permits GET at bucket scope because S3 cannot attach CORS rules to
an object prefix; `ingest/` remains unreadable anonymously through the policy.
HTTPS is required. No database, credential in the app, or additional public
prefix is introduced.

## Upload, verify and configure TV

Use a short CC-BY Big Buck Bunny derivative with the attribution in
`infra/sample-attribution.json`. Preserve explicit limited BT.709 metadata during
encoding; ffmpeg output flags alone can omit primaries/transfer on this host.
The original attribution/source provenance is in `docs/ATTRIBUTION.md`.

The local sample is ignored generated media. On a clean checkout, obtain the
checksum-pinned official source described in `docs/ATTRIBUTION.md`, then create
the quiet opening without playback (replace `SOURCE.mov` with that file):

```sh
mkdir -p synth_out/s7/ccby
ffmpeg -nostdin -i SOURCE.mov -t 3 -an -c:v libx264 -pix_fmt yuv420p \
  -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709 \
  -x264-params 'colorprim=bt709:transfer=bt709:colormatrix=bt709' \
  synth_out/s7/ccby/bbb-opening.mp4
```

Encoder versions/settings may change the output hash; the upload tool binds the
tracks to the actual bytes and does not assume the earlier sample's hash.

```sh
uv sync --directory infra --locked
uv run --directory infra python smoke.py --bucket YOUR_BUCKET --region YOUR_REGION \
  --source ../synth_out/s7/ccby/bbb-opening.mp4 --attribution sample-attribution.json \
  --output ../docs/s7/live-validation.json
```

The smoke tool waits for catalog inclusion, downloads and validates all three
tracks/source bindings, then requires anonymous ingest HTTP 403 and public video
HTTP 200. It records actual catalog-update latency. It never starts raw playback.
Copy the stack's `CatalogUrl` output into the public build-time configuration:

```sh
NOSTROBE_CATALOG_URL=https://YOUR_BUCKET.s3.YOUR_REGION.amazonaws.com/public/catalog.json \
  npm --prefix tv run build:release
```

Without this variable a build regenerates the existing local demo configuration.
The URL must be HTTPS with no user info, query or fragment. Install/run the
Release build on the VVD and verify catalog selection and protected playback.
S6's previously measured video-fluidity/drop limitation remains open.

## Measurements and costs

No AWS profile, credentials or region was available for this session. Live
catalog latency, Lambda speed, billed cost per analyzed hour, anonymous bucket
permission checks and cloud teardown are **not measured**. Do not substitute
local host timings for Lambda observations. See `docs/S7_REPORT.md` and
`engine/eval/RESULTS.md` for separate local/container evidence.

For each real run retain the published status metrics, matching CloudWatch REPORT
request id / Billed Duration / Max Memory Used, region, image digest and price
retrieval date. Lambda real-time multiplier is video duration / handler elapsed
seconds. Compute cost from actual billed seconds, 3008/1024 GiB memory, billed
request count and temporary storage beyond the free allocation using that
region's current [AWS Lambda prices](https://aws.amazon.com/lambda/pricing/).
Normalize total measured cost by `video_duration_s / 3600`. Separately report
S3 requests/storage/egress, CloudWatch and ECR costs; do not label a Lambda-only
estimate as total pipeline cost. Record these observations in RESULTS.md once
available. Check that the hackathon credit is active in the intended account.
Kiro was not used; no Kiro participation claim is made.

## Teardown

For this disposable test stack, verify the bucket/stack name, then:

```sh
aws s3 rm s3://YOUR_BUCKET --recursive
sam delete --stack-name YOUR_STACK --region YOUR_REGION
```

The bucket is unversioned, so emptying it permits stack deletion. SAM can prompt
to remove its managed image repository and artifacts; remove only resources
belonging to this test deployment. Confirm CloudFormation DELETE_COMPLETE and
that the test bucket/function are absent. Keep validation reports locally. Tear
down while idle. This procedure is documented but has not been executed without
AWS authentication; no resources were deployed during the local build.
