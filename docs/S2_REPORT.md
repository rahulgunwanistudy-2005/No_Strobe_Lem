# Session 2 detection report

Verified 2026-10-04. Detection and synthetic accuracy gates pass. The requested
20× detection-speed target is **unmet**; this limitation is not a passed gate.
No mitigation or verified HazardTrack is produced in this session.

## Built

- Vectorized running-extreme/threshold detection, including pre-change startup
  extrema and observed red color endpoints, with a bounded 64-entry
  per-cell timestamp ring. Monotone crossings are coalesced for flash rate
  counting. Opposing transitions, retroactive first-flash inclusion, spacing
  exclusion and exact trailing-window expiry share one counting implementation.
- SDR luma detection; linear-BT.709 saturated-red/chromaticity detection;
  global area and every valid local window via summed-area tables; streaming
  interval construction, strict gap merging and peak statistics; prolonged
  flashing warnings. Frozen profile parameters and their stable hashes remain
  unchanged from S1.
- One ffmpeg decode with synchronized Y/RGB branches feeds all three profiles.
  Linear-light averaging uses the S1 640×360 decode / 160×90 analysis grid.
  Lookup tables, contiguous block sums, empty/full-mask fast paths and batched
  flash history reduce repeated work. No loops run over individual image cells.
- `nostrobe analyze VIDEO --detect-only [--profile all|broadcast|local|kids]
  [--output events.json]`, plus `analyze_detect` / `analyze_detect_all` Python
  APIs and a cell-array entry point for later verifier simulation.
- Detection JSON has a distinct format, `verified: false`, parameter hashes
  and per-profile events. HazardTrack extensions and input-video overwrite
  are refused before analysis. Full analysis, verification and publishing
  continue to refuse explicitly pending S3.
- RGB analysis refuses missing/non-BT.709 transfer/primaries/matrix metadata.
  The existing luma-only reader retains its broader tagged SDR support.
- Reproducible numeric-only benchmark harness and saved film events;
  deterministic property, boundary, codec and resolution tests. Raw hazard
  clips and downloaded footage are not committed or played.

## Verification

From `engine/`:

```sh
uv run ruff check
uv run ruff format --check
uv run mypy --strict src
uv run pytest -q
```

Lint/format pass for 54 Python files; strict types pass for 38 source files.
The final full-suite run passed **338 tests in 299.97 s**. This includes
startup-extrema regressions for both luma directions and red flashing at all
five frame rates, and the non-BT.709 input regression.
`pytest --collect-only -q` confirms 338 tests in the final state.

From the repo root, `npm run types:check && npm run typecheck` pass.
Schema/TypeScript drift checks also pass inside pytest. `git diff --check`
passes. Later TV eslint/Jest/device gates do not apply to this S2 scope.

All 16 S1 smoke clips were encoded and analyzed at each of
24/25/30/50/60 fps: **80 videos, 240 profile outcomes**. S1 synthesis,
analytic truth and the committed smoke manifest were not changed.

| Profile | Expected fail cases | Expected pass cases | Missed hazards | False alarms |
|---|---:|---:|---:|---:|
| Broadcast | 35 | 45 | 0 | 0 |
| Local | 40 | 40 | 0 | 0 |
| Kids | 50 | 30 | 0 | 0 |

Broadcast uses the unchanged S1 analytic truth. Local additionally expects
failure for the concentrated 24% rectangle; Kids additionally expects the
3 flashes/s and isolated-triple cases. These are documented product policies,
not newly attributed broadcast rules. Every must-fail interval meets IoU
≥0.9 against the relevant profile timing. Kids' earlier onset uses an
independent sampled >4-change oracle rather than Broadcast's >6 onset.

Additional checks cover exact luminance/area/spacing/red-ratio/chroma
boundaries, both saturated endpoints, isolated flashes, monotone ramps,
seeded noise, extended-duration strictness, border windows, variable interval
PTS, input errors, bounded counter overflow and cross-cell independence.
Properties cover subthreshold differences, separated isolated bursts,
and encoded 720p/1080p timing invariance within one frame. Combined Y/RGB
frames and PTS match independent decodes byte for byte. Frame-batched rate
counts match per-cell rings, including retroactive timestamps and expiry.

## Performance

Benchmark command:

```sh
cd engine
uv run python eval/benchmark_detection.py \
  /tmp/nostrobe-s2-sources/big_buck_bunny_1080p_h264.mov \
  --output ../docs/s2_benchmark.json
```

The downloaded file is temporary; obtain it from the official source linked
in ATTRIBUTION.md to rerun. Host: Apple M1, 8 GiB RAM, macOS 26.3 arm64;
Python 3.12.11; ffmpeg/ffprobe 7.1.1. Input: 1920×1080, 24 fps,
596.458333 s, 14,315 frames. Three profiles share one pass; decoder/filter
threads are each restricted to one.

| Final measurement | Result |
|---|---:|
| End-to-end wall time | 257.683 s |
| End-to-end throughput | 2.315× real-time |
| Detector-only wall time | 122.677 s |
| Detector-only wall throughput | 4.862× real-time |
| Detector CPU time | 112.547 s |
| Detector throughput per CPU second | 5.300× real-time |
| Requested detector target | 20× (unmet) |

Measurements include concurrent host/test activity and are not isolated
hardware claims. Timing covers the frame pipeline and excludes the first
standalone metadata probe and Python startup. Source hashes, machine/tool details, CPU breakdowns and
all output events are saved in s2_benchmark.json. Profiling identified curve
interpolation, spatial averaging and timestamp/area operations. Optimization
reduced the initial exploratory 348.530 s wall run to the final run above;
these different host loads and startup corrections are not a controlled
speedup experiment. Batched
histories preserve the previous film events exactly.

The film produces 6 Broadcast fail/11 warn, 29 Local fail/72 warn and
40 Kids fail/109 warn events. All fails are luma events. These are unreviewed
flags, **not** verified ground truth or a clean-control false-alarm rate.
Further trace review and broader evaluation belong to S4. They are retained
in the measurement artifact rather than hidden or labeled safe.

## Source corrections and scope limits

Re-read ITU-R BT.1702-3 Annex 1 Guideline 1, Ofcom Section 2 Guidance Notes
Issue Twelve Annex 1 §§2/3/3.1.1, and WCAG 2.2 flash-threshold Notes 2/3.
URLs and fetched-content hashes are in SOURCES.json. The source's SDR
criterion governs over the brief's HDR-relative shorthand; red endpoints and
pairing govern over the brief's entering/leaving-only wording. Fixed spacing,
per-cell counting, local area, black chromaticity convention, warning
proximity and Kids limits remain labeled product interpretations in
INTERPRETATIONS.md. No standards-exact certification claim is made.

An unrestricted “add isolated flashes to any clip without adding a fail”
property is false when added flashes join an existing burst. The valid
separated-burst property is tested. Kids' >4-change limit also conflicts with
an isolated-triple-pass guarantee; Broadcast/Local retain that guarantee.
A 0.34 s period is spacing-eligible but still below 3 flashes/s, so spacing
eligibility alone does not imply failure.

The measured synthetic pass is specific to this suite, grid, source tagging
and documented interpretation. It does not establish arbitrary-content
accuracy, medical safety or certification. Spatial patterns, HDR, broader
footage, PEAT cross-checks, mitigation/verifier, portable track publishing,
TV/device sync/compositing, AWS and S7 OSS extraction remain later sessions.
Performance needs further work before production throughput claims.

## Repository delivery

Changes are committed in logical planning, implementation, optimization,
validation and documentation stages. The user's explicit commit instruction
overrides the bible's manual-commit default. No attribution trailers are
added; history is not rewritten and no public push is performed.
