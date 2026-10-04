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

- [ ] Re-read ITU/Ofcom/WCAG sources and record detection interpretations.
- [ ] Build vectorized opposing-change and bounded rate counters, luma/red
  detection, summed-area rules, interval merging and extended warnings.
- [ ] Wire one decoding pass shared by all profiles to analyze --detect-only;
  emit detection results only, with no verified-track claim.
- [ ] Add independent boundary/property/encoded integration checks across
  24/25/30/50/60 fps; preserve S1 truth and investigate every mismatch.
- [ ] Benchmark a ten-minute 1080p CC-BY film, profile bottlenecks and record
  actual machine/tool versions and throughput.
- [ ] Self-review; run lint/format/strict types/full tests and contract checks;
  document results, friction, limitations and commit each finished stage.
