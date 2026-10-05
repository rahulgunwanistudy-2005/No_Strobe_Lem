# Detection performance follow-up — 2026-10-05

The S2 detection target of at least **20× real-time per core is met** on the
original full-length 1080p Big Buck Bunny film, at the 160×90 analysis grid,
with luminance, saturated-red and extended detection for all three profiles.
Both cold and warm compiler-cache runs pass the stricter benchmark gate of
at least 20× by **both detector elapsed time and detector CPU time**.

| Measurement | Detector elapsed | Detector CPU | Elapsed speed | CPU speed | Decode + detection elapsed |
|---|---:|---:|---:|---:|---:|
| Historical S2 | 122.677 s | 112.547 s | 4.862× | 5.300× | 257.683 s / 2.315× |
| Cold compiler cache | 25.833 s | 24.561 s | **23.089×** | **24.285×** | 147.504 s / 4.044× |
| Warm compiler cache | 23.677 s | 22.566 s | **25.191×** | **26.432×** | 146.283 s / 4.077× |

Measurements: [cold](../engine/eval/performance/cold.json),
[warm](../engine/eval/performance/warm.json),
[hashes and event-equivalence proof](../engine/eval/performance/proof.json).
The historical S2 run is context, rather than a controlled simultaneous A/B
experiment. Host activity varies; these are actual observations, not a speed
guarantee on every machine or under arbitrary contention.

## Scope and method

- Apple M1, 8 GiB RAM, macOS arm64; Python 3.12.11, NumPy 2.5.3,
  Numba 0.67.0, llvmlite 0.49.0 and ffmpeg 7.1.1.
- Unmodified official source: 1920×1080, 24 fps, 596.458333 s;
  **every one of its 14,315 frames** is decoded and checked in each run.
  Source SHA-256:
  `dc2146a2b1172def56730143ad80cd1825b7fad15f1fc9c23a4e7d01a741ac11`.
- Detection timing includes every pipeline update and event finalization.
  The cold run starts with a newly created, empty compiler-cache directory;
  first-call compilation is charged to detection. Six compiled cache files
  were created. The warm run loads previously compiled kernels.
- Kernels use one core, with `parallel=False` and `fastmath=False`. The decoder
  and filter are configured with one thread each. Detector CPU time is the
  Python process's CPU time, including its lightweight timestamp reader;
  ffmpeg CPU time is recorded separately.
- Decode and cell conversion remain separately measured. Spatial samples are
  still decoded at 640×360 and converted to luminance/linear RGB before 4×4
  averaging to 160×90. No profile, red rule, frame or cell is omitted.
- The 20× target concerns **detection**. End-to-end decoding plus detection is
  about 4×. Full veil solving/report generation has additional cost and was
  not assigned a new 20× target or rebenchmarked here. Film flags remain
  unadjudicated; this is not a clean-film accuracy or certification claim.

## Changes and accuracy checks

Strict compiled kernels replace repeated temporary arrays in SDR crossings,
red excursion tracking, opposing-edge pairing, chromaticity finishing and
summed-area scans. Exact masks, maxima and area calculations are shared across
profiles. Retroactive timestamp insertion updates only the selected cells.
The unused duplicate luma-crossing history is omitted from the pipeline;
standalone ChangeDetector retains its original timestamp ring.

The original NumPy RGB-to-XYZ matrix product remains intact. A trial transpose
changed small-grid rounding and was rejected. The frozen dd980e5 implementation
checks exact state, counters and timestamp masks at all five frame rates,
irregular timestamps, strict boundaries, all borders and the full spatial grid.
Both complete film runs reproduce **every S4 event field exactly**.

The original S4 reports and two-run determinism proof remain bound to their
original source revision and retain their historical timings. A separate audit
reruns detection and full offset verification of the saved S4 tracks. It checks
actual source checksums and unchanged decoder/generator/oracle/profile modules
before loading original lossless byte samples. It retains the original truth,
veils and viewing costs; it does not reuse old verification outcomes or claim
fresh veil solving or new full-analyze timings.

The [fresh saved-track audit](../engine/eval/performance/regression.json)
completed all **325 synthetic/composite cases and 975 profile tracks**, including
**355 tracks with veils**. Every detected event is exactly unchanged; all tracks
pass fresh full-file verification at −150/0/+150 ms, with zero residual failures
and zero unresolved segments. Against the unchanged independent truth, FN=0
and FP=0 in every profile (325 verified tracks per profile). The audit took
716.129 s, including loading prepared samples and repeated verification; it is
not a new solver benchmark. Its hash is recorded in the performance proof.

Quality checks pass: **402 tests in 348.70 s**, lint and formatting, strict
Python types across 52 source files, schema/generated-TypeScript drift, and
TypeScript type checking. No original truth, seed, threshold, parameter hash or
publication gate was changed.

## Reproduce

Sync dependencies with `(cd engine && uv sync --locked)`, then run from the
repository root:

```sh
engine/.venv/bin/python engine/eval/benchmark_detection.py \
  synth_out/s4/sources/big_buck_bunny_1080p_h264.mov \
  --output /tmp/nostrobe-warm.json --jit-cache-mode warm

nostrobe_jit_cache=$(mktemp -d)
NUMBA_CACHE_DIR="$nostrobe_jit_cache" engine/.venv/bin/python \
  engine/eval/benchmark_detection.py \
  synth_out/s4/sources/big_buck_bunny_1080p_h264.mov \
  --output /tmp/nostrobe-cold.json --jit-cache-mode cold
```

A benchmark returns exit 0 only when both detector speed measures reach 20×;
otherwise it retains its actual measurements and returns exit 2. The cache-mode
label describes the supplied environment; use a newly created directory for
cold measurements and an already populated cache for warm measurements.

To rerun the separate saved-track audit with the original prepared input cache:

```sh
engine/.venv/bin/python engine/eval/revalidate_performance.py \
  --baseline engine/eval/results.json \
  --decoded synth_out/s4/evidence/08c771e187fe74f7c8e76855a325c3ebdd23c4c09f5cc1a8c42a520d07748671/decoded \
  --output /tmp/nostrobe-performance-regression.json
```

The audit refuses missing or changed input-cache producers and source checksums,
changed events, or any failing saved veil. Prepared input archives remain
ignored; dangerous source clips must not be played for review.
