# Session 1 plan

Scope: execute the supplied S1 prompt. Later sessions are gated and not authorized by a supplied session prompt. User authorizes systematic commits without attribution trailers, overriding CLAUDE.md §22.2.

- [x] Decide the device lane on macOS 26.3 arm64; install official Vega tools, run version and virtual-device hello-world checks; record actual blockers.
- [x] Verify ITU-R BT.1702-3/-2 and WCAG definitions; record source discrepancies.
- [x] Scaffold the monorepo, Python 3.12 project and exact dependency lockfiles; leave TV as placeholder until S5.
- [x] Implement validated frozen contracts, deterministic profile hashes, schema and generated TypeScript contract workflow.
- [x] Implement sourced SDR curve, color conversions, bounded ffmpeg decoding, and seeded synthetic primitives with analytic truth sidecars.
- [x] Verify contracts, luminance anchors, decode round-trips, spatial averaging, generator timing/tags, lint and strict types.
- [x] Self-review, document measured results and limitations, and commit logical stages. S1 device gate passed by build/run and lifecycle VISIBLE-state verification.

Lane A selected: macOS 26.3 arm64 is a supported host family; 31 GiB available before install. Lane B is reserved for inability to run Vega; switching architecture requires a decision, not an invented device pass.

## Completion

S1 gates passed on 2026-10-04. See docs/S1_REPORT.md. S2 was not started.
The desktop was locked, so visual inspection was unavailable; the device lifecycle manager confirmed the app was visible before the device was stopped.

# Session 2 plan

Scope: execute S2_detection_engine.md under the project bible, with source
corrections preserved from S1. The user's explicit commit request overrides
the manual-commit default. Commit logical stages without attribution trailers.

- [x] Re-read ITU/Ofcom/WCAG sources and record detection interpretations.
- [x] Build vectorized opposing-change and bounded rate counters, luma/red
  detection, summed-area rules, interval merging and extended warnings.
- [x] Wire one decoding pass shared by all profiles to analyze --detect-only;
  emit detection results only, with no verified-track claim.
- [x] Add independent boundary/property/encoded integration checks across
  24/25/30/50/60 fps; preserve S1 truth and investigate every mismatch.
- [x] Benchmark a ten-minute 1080p CC-BY film, profile bottlenecks and record
  actual machine/tool versions and throughput.
- [x] Self-review; run lint/format/strict types/full tests and contract checks;
  document results, friction, limitations and commit each finished stage.

## S2 results

Detection/accuracy/quality gates are verified; the 20× performance target is
**not met**. See docs/S2_REPORT.md for scope and limits.

- Final full-suite run: 338 tests passed in 299.97 s. Startup luma/red
  regressions and non-BT.709 metadata refusal are included.
- All 80 encoded smoke cases pass at 24/25/30/50/60 fps. Per-profile expected
  positives: Broadcast 35, Local 40, Kids 50; FN=0 and FP=0 against those
  documented expectations. Interval IoU >=0.9 on every must-fail case with
  independent profile timing. S1 generator/truth/manifest remain unchanged.
- ruff check/format, strict mypy (38 source files), schema/generated-type
  drift checks and TypeScript typecheck pass.
- Apple M1, 8 GiB RAM, macOS 26.3 arm64, Python 3.12.11, ffmpeg 7.1.1;
  1080p/24 fps Big Buck Bunny, 596.458333 s, 14,315 frames. All profiles,
  one decoding pass, one ffmpeg decoder/filter thread.
- Final benchmark: 257.683 s wall, 2.315× end-to-end; 122.677 s detector wall,
  4.862× detector throughput; 112.547 s detector CPU, 5.300× per CPU second.
  Includes concurrent host/test activity; no isolated-system claim.
- Profiling improvements: curve lookup tables, contiguous block means,
  empty/full-area shortcuts, expiry caching, and frame-batched flash histories.
  Film events are identical before/after the latter optimization.
- Film flags: Broadcast 6 fail/11 warn, Local 29 fail/72 warn, Kids 40 fail/
  109 warn. These are unreviewed detections, not an accuracy/clean-control score.
- S3 mitigation/verifier/publishing, S4 broader evaluation and film-flag review,
  TV/media calibration and AWS remain future sessions. No verified track is
  emitted by S2. Performance requires further work before production claims.
