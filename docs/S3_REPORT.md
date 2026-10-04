# Session 3 report — 2026-10-04

Scope: the supplied S3 veil/verifier/track/CLI/report session, under the existing
project bible and S2 standards corrections. The user's explicit commit request
supersedes the bible's manual-commit default. Commits contain no attribution
trailers. S4 evaluation, device calibration, TV implementation and AWS remain
outside this session.

## Built

- Validated display-code blending on original pre-average Y/RGB samples;
  continuous ramps, deterministic overlap resolution, clamped/merged plateaus.
- Source-SHA-keyed memory-mapped 32-frame decode shards with original PTS.
  Exact row/column replication and byte-identical cell-history grouping reduce
  local checking work; original spatial counts are restored before area rules.
- Per-segment gray/alpha search, 0.02 coarse steps, <=0.005 bracket refinement,
  actual luminance-distortion selection and deterministic ties. Local checks
  include 1.5 s beyond ramp supports, with longer persistence history for
  extended warnings; Kids warnings must be suppressed or explicitly unresolved.
- Complete-file detector verification at -0.15/0/+0.15 s, one residual-driven
  retry, explicit unresolved reasons and debug-only JSON for failing profiles.
  Source events remain intact during retry; stale verified artifacts are removed.
- Canonical JSON and strict metadata WebVTT, preserving exact veil payloads and
  event provenance. Generated schema/TypeScript include optional unresolved
  reasons and mean luminance cost without breaking old contract fixtures.
- Duration-weighted active opacity/luminance cost, support-union runtime and
  per-kind event counts. Default all-profile analyze, profile restriction,
  video-bound re-verification, report and schema commands; documented exits.
- Static self-contained HTML with event tables, opacity timelines, before/after
  traces of cells with maximum qualifying-change count, verification, parameter
  hash, source hash and fixed disclaimer. No source frames/video are embedded.
- Portable HTML5 overlay reference with the same ramp/overlap semantics and
  refusal of unverified artifacts; it never starts playback.

## Verified

- Final full test suite: **359 passed in 319.50 s**. Includes unchanged S1/S2
  truth/boundaries, compositing, offsets/ramps, exact grouping equivalence,
  all-profile CLI, source binding, stale artifact removal, one retry and
  unresolved publication refusal. The extended-warning regression confirms
  that fixed timing can require refusal even when the fail-only verifier passes.
- `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict src`
  pass; 42 source files checked. `npm run types:check`, `npm run typecheck` and
  schema drift checks pass. No dependency versions were changed.
- JSON/WebVTT round trips preserve model data and exact veil floats. The strict
  parser rejects malformed headers, metadata, timestamps, cue timing and ids.
  A separate WebVTT library is not installed; that optional comparison was not
  run.
- The sample report was inspected in the in-app browser: tables, inline charts,
  source/parameter hashes and disclaimer are readable; no raw media is present.
  Sample artifacts are in ignored `analysis_out/example/`.

## Synthetic mitigation acceptance

All **80 encoded clips × 3 profiles = 240 checks pass** at every configured
sync offset, with **zero unresolved cases** in the available smoke suite.
Detection agrees with unchanged S1/S2 profile expectations (FN=0, FP=0).
All 45 Broadcast must-pass cases receive zero veils. Every profile with no
eligible event receives zero veils; no opacity occurs outside cue supports.
The full run took 1,684.006 s alongside other validation/benchmark activity.
Per-case measurements are committed in `s3_synthetic.json`.

Viewing cost below is the mean of per-clip active-support metrics on each
profile's must-fail set, including ramps:

| Profile | Must-fail cases | Mean opacity | Mean absolute ΔL (cd/m²) | Mean veiled runtime |
|---|---:|---:|---:|---:|
| Broadcast | 35 | 0.4201 | 23.1552 | 91.15% |
| Local | 40 | 0.4295 | 24.9873 | 91.21% |
| Kids | 50 | 0.4636 | 31.1950 | 97.11% |

These short stimuli flash throughout most of their duration. Kids additionally
veils five warning-only isolated-double cases; all 55 eligible Kids cases
resolve. The separate seven-second extended-warning regression intentionally
requires an unresolved result under the fixed timing configuration.
The harness retains S1 Broadcast truth and the documented S2 Local/Kids
expectations. A Broadcast must-pass clip must receive zero veils. Local may
fail a 24% global-area clip, and Kids intentionally mitigates its warnings and
stricter failures; relabeling these as Broadcast false positives would be wrong.
Every profile with no eligible event must receive zero veils.

Reproduce: `cd engine && uv run python eval/verify_mitigation.py --output
../docs/s3_synthetic.json`. This tests the full currently implemented smoke
suite at 24/25/30/50/60 fps; it does not replace the broader S4 suite.

## Approximately ten-minute film

The complete Broadcast pipeline finished in **3,015.374 s (50.26 min)**,
**0.1978x real-time**, with a warm decode cache. Measurements are committed in
`s3_benchmark.json`. It produced debug JSON and a complete trace report;
**publication was refused** with three unresolved segments:

| Interval (s) | Reason |
|---|---|
| 196.166667–196.500000 | Residual failure after full-file verification and one retry |
| 442.958333–443.083333 | Residual failure after full-file verification and one retry |
| 553.333333–557.125000 | No candidate passed the conservative local check within max_alpha |

The attempted four veils cover 2.2424% of runtime, with mean active opacity
0.4677 and mean active absolute luminance distortion 14.1429 cd/m². These are
costs of an **unresolved attempt**, not a published mitigation. The two residual
failures demonstrate why segment-local success cannot replace whole-file
verification. The approximately ten-minute completion gate was exercised;
real-film mitigation/throughput remain limitations.

Host: macOS 26.3 arm64, Python 3.12.11, ffmpeg/ffprobe 7.1.1. The run began
before the equivalent luma-only distortion shortcut was added; recorded time
includes the earlier cost calculation and concurrent validation. It is a
measured run, not an isolated speed claim for the final source revision. The film is the unchanged 596.458333 s, 1080p/24 fps Big
Buck Bunny source credited in `ATTRIBUTION.md`. A preceding interrupted run
prepared the decode cache; the final benchmark starts warm and runs alongside
synthetic/test activity. The timing is not a cold-start or isolated-host claim.

Reproduce with `engine/eval/benchmark_mitigation.py VIDEO --out DIR
--measurement JSON --profile broadcast`. The complete pipeline includes solve,
whole-file verification, publication gating, statistics and trace-report
rendering. Local/Kids film throughput is not measured. Original film flags
remain unreviewed, so no clean-control accuracy claim is made.

## Remaining limits

- This is finite-grid distortion minimization under the documented display-code
  simulation, not a continuous optimality proof or measured device result.
- The default 0.15 s sync tolerance and compositing fit await S5 measurements.
  The S2 20x detection-throughput target was not met; S3 does not claim it passed.
- Caching retains roughly 0.88 MiB/frame on disk. The approximately ten-minute
  film cache takes about 12.3 GiB; memory stays bounded through mapped shards.
  The generated film cache was removed after measurement to restore disk space;
  reports, numerical results and the original credited source were preserved.
- The broader S4 realistic composites, clean-control review, full evaluation
  metrics and PEAT comparison remain pending. No medical/certification claim,
  device result, AWS deployment or new media-support scope is asserted.
