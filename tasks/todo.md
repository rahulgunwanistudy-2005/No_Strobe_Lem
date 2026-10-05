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

# Session 3 plan

Scope: execute S3_veil_verifier_track_cli.md. User authorizes logical commits
without attribution tags. Preserve S2 standards corrections and existing truth.

- [x] Implement validated display-code compositing, deterministic ramps and
  padded/merged segments; document shared playback semantics.
- [x] Cache source-hash-keyed decoded samples without losing subcell variation;
  implement all-offset full-detector verification and distortion search.
- [x] Add final whole-file verification, one retry and explicit unresolved reasons;
  refuse publication of failing tracks.
- [x] Implement JSON/WebVTT readers/writers, stats, CLI and trace-only HTML report.
- [x] Test encoded synthetic cases at all supported frame rates, record viewing
  costs, run a ten-minute film analysis and record actual time/limitations.
- [x] Self-review, pass quality/contract gates, document outcomes and commit stages.


## S3 results

Implemented the S3 engine/contract/CLI/report scope. See docs/S3_REPORT.md.

- 359 tests passed in 319.50 s; lint/format, strict mypy, schema/generated-type
  drift and TypeScript checks pass. Static sample report inspected visually.
- All 80 encoded smoke clips across five fps values and three profiles pass:
  240 verifier outcomes, zero unresolved smoke cases, FN=0/FP=0 against unchanged
  profile expectations. Broadcast must-pass clips receive zero veils.
- The separate Kids extended-warning regression correctly refuses publication
  when fixed timing cannot clear the trailing history before the warning.
- The 596.458333 s Broadcast film pipeline completed in 3,015.374 s from a warm
  cache, with three unresolved segments and two final residual failures. Only
  debug JSON/report were written. No clean-control accuracy claim is made.
- Real-content mitigation/throughput, the wider S4 suite, S5 device calibration,
  TV and AWS remain deferred. The original source is preserved; the generated
  12.3 GiB benchmark cache was removed. No history rewrite or external publishing.

# Session 4 plan

Scope: implement S4_evaluation.md; user authorizes systematic commits without
attribution tags, overriding the manual-commit default. Preserve existing truth.

- [x] Define versioned seeded boundary/shape suites and independent profile truth.
- [x] Verify official Blender licenses, pin downloads by checksum, composite five
  realistic scenarios, retain the eligible unmodified film control and record
  source-metadata exclusions.
- [x] Implement checksum decode caching, per-profile analysis, interval/confusion/
  verifier/viewing-cost metrics, honest clean traces and reproducible reports.
- [x] Persist provenance-bound timing observations separately from deterministic
  accuracy; invalidate caches when code, manifest, source or parameters change.
- [x] Run the full suite, investigate misses without changing original truth, verify repeat
  determinism and required quality gates; document evidence and commit stages.

## S4 results

Implemented the supplied S4 scope. See docs/S4_REPORT.md and the sole
submission-number sources engine/eval/RESULTS.md / results.json.

- Two complete default runs each returned exit 0 with 978 profile outcomes;
  both JSON and Markdown are byte-identical. No --resume or excluded timestamp
  field was used. Provenance and hashes are in engine/eval/determinism.json.
- 120 boundaries, 200 seeded shape variations and five realistic composites:
  FN=0 and FP=0 against independent per-profile truth; all 975 tracks verified
  under simulated −150/0/+150 ms, including all 355 tracks with veils;
  unresolved=0. There are 305 distinct source checksums across 326 case files.
- 374 tests passed in 734.26 s; lint/format, strict types (50 source files),
  schema/generated-TypeScript drift and TypeScript checks pass.
- The SDR oracle source correction and composite encoder tag failure are
  preserved as audits. No original S1 truth, source seed or production detector
  threshold was changed to fit a result; decoder checks remain strict.
- One eligible unmodified full-film control was streamed per run. Its flags
  and trace are retained and explained as unadjudicated motion/text candidates;
  it is excluded from confusion scores. Tears of Steel's inspected originals
  lack required source color tags and are excluded from unmodified controls.
- The 20× performance target remains unmet; host timings include prepared
  synthetic samples and concurrent host activity. PEAT was not run. Natural-film
  accuracy, measured device timing/compositing, TV and AWS remain open S5+ work.

# Performance follow-up plan

Scope: meet S2's >=20x real-time detection per core on the full 596.458333 s
1080p CC-BY film, using the 160x90 grid and all three profiles. User authorizes
systematic commits without attribution tags. Preserve standards, original truth,
red detection, spatial fidelity and mitigation verification.

- [x] Profile a representative decoded film sample and establish a current baseline.
- [x] Optimize measured hot spots with exact-output differential regressions.
- [x] Measure the entire original film, detector wall/CPU and end-to-end costs;
  require >=20x detector throughput and report remaining processing costs.
- [x] Run accuracy/verifier and quality gates; refresh provenance-bound evaluation
  evidence where engine changes invalidate the prior evidence.
- [x] Review, document performance evidence and commit logical stages.


## Performance follow-up results

The >=20x all-profile detection target is met on the original 596.458333 s,
14,315-frame 1080p film at the full 160x90 grid. See docs/PERFORMANCE.md.

- Cold JIT cache: detector wall 25.833 s / 23.089x; CPU 24.561 s / 24.285x.
- Warm JIT cache: detector wall 23.677 s / 25.191x; CPU 22.566 s / 26.432x.
- Both benchmark gates return exit 0; every full-film event field matches S4.
  Apple M1, 8 GiB RAM; single-core kernels, strict arithmetic, all profiles.
- 402 tests pass in 348.70 s; lint/format, strict types (52 source files),
  schema/generated-type drift and TypeScript checks pass.
- Fresh audit: 325 cases / 975 tracks, exact source-event equality, FN=FP=0
  all profiles; all saved veils reverified at -150/0/+150 ms, including 355
  tracks with veils; zero residual failures or unresolved segments.
- Original S4 reports, source truth and two-run determinism proof are retained
  unchanged. The new audit has its own source/code hashes and fresh verifier
  outcomes. It does not claim fresh solving or new full-analyze timings.
- Decode + detection remains about 4x end-to-end; full mitigation has separate
  cost. PEAT, natural-film adjudication and S5 device/cloud work remain open.
- Source, tools, benchmark evidence, audit and documentation are committed in
  logical stages without attribution trailers or history rewrites.

# Session 5 plan

Scope: execute S5_vega_player_veil_sync.md using Lane A and the installed
Vega SDK. User authorizes systematic commits without attribution trailers,
overriding CLAUDE.md §22.2. Device measurements must come from recordings;
no simulated value will be labeled as measured.

- [x] Generate the current Vega template, pin dependencies and move generated
  HazardTrack types into tv/src/types with drift checks.
- [x] Implement the isolated W3C player/surface lifecycle, validated track loader,
  drift-corrected clock, deterministic scheduler and minimal protected player.
- [x] Export a Python/TypeScript timeline conformance fixture (500 samples);
  test clock, scheduler, loading, lifecycle and platform-import boundaries.
- [x] Generate and numerically preflight nonhazardous sync/compositing stimuli,
  plus bounded recording-analysis tools and an isolated Debug lab.
- [ ] Obtain real >=60 fps VVD recordings for timing, seeks/pause/resume and
  compositing; visual QA and recording access remain blocked.
- [ ] Apply the measured tolerance/model only after valid capture, rerun S3/S4
  verification, preserve historical evidence and report fresh gates honestly.
- [x] Self-review, run quality/build/device gates, document reproduced friction
  and product feedback, and commit logical stages.


## S5 results

Player/calibration infrastructure is committed; S5 acceptance is **incomplete**.
See docs/S5_REPORT.md and engine/eval/s5_calibration_status.json.

- 408 engine tests and 30 TV tests passed; six calibration/conformance tests
  rechecked after final measurement-tool refinements. Quality/type/drift gates
  and Release/Debug builds pass. Release excludes calibration media.
- Actual VVD native playback confirmed loadedmetadata/canplay, play/playing,
  timeupdate, pause, seeked and ended. Rendered layout/opacity are unverified.
- Fresh 975-track audit passes at the existing simulated ±150 ms tolerance,
  FN=FP=0, exact events, zero unresolved/residuals. No fresh solver claim.
- Screen capture receives no usable frames; device screenshots/capture did
  not yield valid evidence. Real sync/compositing reports are absent, engine
  parameters unchanged, and measured-tolerance S3/S4 rerun remains open.
- No AI attribution tags, external publication or AWS deployment.

## S5 continuation — device measurements

- [x] Recheck host/device capture availability and obtain real rendered frames.
- [x] Complete visual QA and >=60 fps steady/seek/pause-resume sync captures.
- [x] Measure all compositor cases; apply the measured tolerance/model.
- [ ] Rerun S3/S4 and quality/build gates; update results and commit evidence.
