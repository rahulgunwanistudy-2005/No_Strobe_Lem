# Session 7 — AWS pipeline and public reference library

Implemented the AWS packaging/ingest/catalog scope and published the separate
Apache-2.0 [hazardtrack repository](https://github.com/rahul-software-dev/hazardtrack)
and [v0.1.0 release](https://github.com/rahul-software-dev/hazardtrack/releases/tag/v0.1.0).
**Live AWS acceptance remains incomplete:** no authenticated profile, credentials
or region was available. No cloud resources were deployed or billed during this
session. The user explicitly authorized systematic commits, overriding the
bible's manual-commit default and prior S6-before-S7 deferral. S6's measured
video-fluidity/drop limitation remains recorded.

## Built

- Thin Lambda entry point; streamed/limited download, strict SDR/BT.709 probe,
  hash-plus-slug content ids and decoded-cache disk preflight.
- Shared decode, three-profile solving/verification, refusal before any video
  or track upload when a profile fails, JSON/WebVTT/report publication, typed
  rejected-input status and structured per-profile metrics.
- Source-notification ETag preconditions; duplicate/stale notification handling;
  ready status committed last; pagination and conditional, listing-derived
  catalog rebuilding. A competing-writer regression proves no lost item.
- SAM bucket/public-prefix policy, HTTPS enforcement, GET-only bucket CORS,
  encryption/public-ACL blocking, scoped S3 IAM, 3008 MB / 900 s / 10 GiB Lambda,
  reserved concurrency two and seven-day logs.
- Pinned Lambda base, hash-pinned runtime dependencies, CI-built library wheel,
  and a minimal static ffmpeg/ffprobe release bundle. Bundle contains official
  source, LGPL license, build recipe and provenance; `Dockerfile.source` retains
  the independently reproducible source build.
- Public spec/schema, detector/solver/verifier/readers/writers, evaluation and
  conformance fixtures, independent CI, contribution guide and browser player.
  Product infra resolves the published git tag/commit; local source/spec export
  matches it. Host SDK acquisition tests and product TypeScript generation are
  excluded from the standalone library, with schema/conformance gates retained.
- Build-time `NOSTROBE_CATALOG_URL`, correct public-prefix catalog routing,
  credentials/query refusal and preserved local default configuration.
- Live-upload/permission smoke tool, actual-image size/read-only/codec check,
  ops/teardown instructions and submission record. Kiro was not used.

## Verified

| Gate | Evidence |
|---|---|
| Published library quality/release | [Tagged CI run](https://github.com/rahul-software-dev/hazardtrack/actions/runs/37441310248): 422 tests, lint/format, strict types, schema/timeline/browser checks and wheel publication pass |
| Product engine | 421 tests at pre-PTS checkpoint; after precision correction, 116 targeted decode/smoke tests pass unchanged, and final tagged Linux CI runs the complete extracted engine suite |
| Pipeline integration | 10 tests against the published git dependency: real encoded SDR input, three-profile/source/VTT binding, failed-profile/HDR/limits refusal, ETag matching/staleness, idempotency, SDK retry and concurrent catalog writes |
| Python quality | Product lint/format/strict types; infra lint/format and strict types for five source/ops modules pass |
| TV/contract | 47 tests / 9 suites; TypeScript, ESLint, generated contract drift and Release build pass |
| Browser reader | 500 shared samples, overlap/ramp semantics, JSON/CRLF WebVTT and invalid/unresolved refusal pass; actual in-app browser playback and mismatch refusal observed |
| Container | Read-only linux/amd64 image with CI wheel; real H.264 CC-BY derivative and H.265 input produce three bound verified tracks; static ELF has no dynamic/interpreter headers |
| SAM | Template lint and normal build pass; clean committed-snapshot build is recorded in S7_VALIDATION.json |

The final container is approximately **902 MB** uncompressed, below the strict
1,000,000,000-byte budget. Exact image ids/size/runtime results are retained in
[container-validation.json](s7/container-validation.json) and
[container-hevc-validation.json](s7/container-hevc-validation.json). ffmpeg 7.1.1
is compiled with only the ingest decoder/filter/output requirements, excluding
network protocols and synthesis encoders. Compiler/package caches are absent
from the runtime image. Hashes, tagged source and CI links are in
[release-lock.json](../infra/release-lock.json).

The local three-second Big Buck Bunny derivative completed the real host
pipeline in 6.155733 s, with zero events and all three profiles verified. This
uses an in-memory S3 adapter on macOS, **not AWS Lambda**. See
[local-ccby-pipeline.json](s7/local-ccby-pipeline.json). Docker timings are slower
under x86 emulation and likewise are not cloud throughput/cost measurements.

The browser fixture uses constant gray with a deliberately added, nonminimal
veil. Real verification accepts its input/output at the current offsets. The
[short capture](s7/web-overlay.mp4) and [observations](s7/web-overlay-samples.json)
show its ramp and plateau without raw strobe. This demonstrates application of
the overlay; it does not establish browser calibration or hazardous-content
accuracy. Native Chrome/Firefox were not separately driven; the in-app browser
was exercised. See [browser validation](BROWSER_VALIDATION.md).

## Corrections and provenance

Ubuntu CI reproduced three exact-3-flashes/s must-pass failures because ffmpeg's
human-readable `pts_time` was rounded. Decoder timing now uses integer PTS and
the filter's rational time base; three exact-boundary regressions and a cache
version bump prevent reuse of rounded histories. All independent truth and
thresholds remain unchanged. The original evaluation/calibration reports stay
historical; S7 does not claim a fresh complete S4 solver evaluation or device
calibration. The final source is independently checked by the release CI.

Initial general-purpose ffmpeg packaging exceeded 1 GB. A smaller source build
passed both codec/runtime gates. SAM's separate builder repeated slow bootstrap
work; the normal image now downloads those tested static binaries with a fixed
SHA-256. Source/license/build provenance remain available. Actual network and
credential-helper issues are recorded in FRICTION_LOG.md.

## Open acceptance gates

- Deploy from the clean checkout with the intended AWS account/profile/region.
- Upload the attributed CC-BY sample; measure actual catalog latency and Lambda
  throughput; retain billed duration, current regional prices and measured costs
  per analyzed video hour in AWS.md and engine/eval/RESULTS.md.
- Require anonymous ingest HTTP 403 and public video HTTP 200 on the real bucket.
- Build with the actual catalog URL and exercise protected playback on VVD.
- Empty/delete this disposable test stack and verify teardown once.

The infrastructure and live smoke/ops steps are ready for these checks. An
unavailable authenticated cloud run is not replaced by local simulations.
