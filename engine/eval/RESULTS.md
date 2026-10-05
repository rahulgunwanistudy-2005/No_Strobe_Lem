# S4 evaluation results

Detection and verifier gate: **PASS**.

Headline numbers (these are the sole submission-number source):

- broadcast: **0 missed hazards** on 96 must-fail clips; 0 false alarms on 229 must-pass clips.
- local: **0 missed hazards** on 108 must-fail clips; 0 false alarms on 217 must-pass clips.
- kids: **0 missed hazards** on 142 must-fail clips; 0 false alarms on 183 must-pass clips.
- 975/975 profile tracks re-verify at −150, 0, +150 ms (default simulation tolerance; not device calibration).
- 0 unresolved segments retained with reasons; publication refused for affected profile tracks.

## Accuracy and interval overlap

| Profile | TP | TN | FP | **FN** | IoU median | IoU p10 |
|---|---:|---:|---:|---:|---:|---:|
| broadcast | 96 | 229 | 0 | **0** | 1.0 | 0.9999998684210526 |
| local | 108 | 217 | 0 | **0** | 1.0 | 0.9999998684210526 |
| kids | 142 | 183 | 0 | **0** | 1.0 | 0.9999998461538698 |

| Suite | Profile | TP | TN | FP | FN |
|---|---|---:|---:|---:|---:|
| boundary | broadcast | 54 | 66 | 0 | 0 |
| boundary | local | 59 | 61 | 0 | 0 |
| boundary | kids | 74 | 46 | 0 | 0 |
| shapes | broadcast | 37 | 163 | 0 | 0 |
| shapes | local | 44 | 156 | 0 | 0 |
| shapes | kids | 63 | 137 | 0 | 0 |
| realistic | broadcast | 5 | 0 | 0 | 0 |
| realistic | local | 5 | 0 | 0 | 0 |
| realistic | kids | 5 | 0 | 0 | 0 |

## Viewing cost and verification

Duration-weighted costs include simulated unresolved fallback veils; they do not imply those tracks can be published.

| Profile | Verified / analyzed | Unresolved segments | Veiled runtime | Mean α during veil support | Mean ΔL cd/m² |
|---|---:|---:|---:|---:|---:|
| broadcast | 325 / 325 | 0 | 0.278428 | 0.377614 | 15.155581 |
| local | 325 / 325 | 0 | 0.312563 | 0.383311 | 16.941004 |
| kids | 325 / 325 | 0 | 0.448651 | 0.387768 | 20.251869 |

## Throughput

All-profile shared passes. Full analyze includes decode/cache loading or packing and detection/solve/verification; it excludes generation, truth calculation and report rendering. Detect includes cell conversion for the synthetic/composite cache runs. Full-film detect below measures detector updates separately. Host was not reserved for benchmarking.

| Suite | Clips | Duration s | Detect × real-time | Full analyze × real-time |
|---|---:|---:|---:|---:|
| boundary | 120 | 350.000000 | 3.8316 | 0.3660 |
| shapes | 200 | 600.000000 | 2.8787 | 0.5100 |
| realistic | 5 | 15.000000 | 2.4114 | 0.0159 |
| clean | 1 | 596.458333 | 6.6304 | not run (detection control) |

## Unmodified film controls

The entire checksum-pinned films are decoded without modification. They have no independently reviewed interval truth and are excluded from confusion scores. Nonzero flags are **unreviewed**, neither confirmed true positives nor established false alarms. Traces show luminance only and never play raw footage. A whole-frame mean can hide local/red hazards; review the per-profile event evidence in results.json before claiming clean-film accuracy.

| Film | Profile | Fail events | Warn events | Trace |
|---|---|---:|---:|---|
| bbb | broadcast | 6 | 11 | [luminance trace](traces/bbb.png) |
| bbb | local | 29 | 72 | [luminance trace](traces/bbb.png) |
| bbb | kids | 40 | 109 | [luminance trace](traces/bbb.png) |

Static reference frames plus numerical traces; no raw playback and no external PEAT adjudication.

- At 196.25 s: Rapid squirrel close-up movement against a bright background.
- At 421.0 s: Moving squirrel and leaves against bright sky and spikes.
- At 443.0 s: Moving high-contrast branches and leaves.
- At 445.0 s: Moving foliage and a squirrel over the spikes.
- At 555.0 s: Dense white-on-black credits with an animated squirrel.
- At 559.0 s: Dense scrolling white-on-black credits.

The flags coincide with high-contrast motion, foliage and credits, rather than an assumed clean zero-flash source. The detector measures cell luminance reversals, so motion can create qualifying excursions. These are candidate motion/text false alarms; they have not been adjudicated as confirmed false alarms or true broadcast violations. Local and Kids add smaller-area/lower-count detections and remain unadjudicated. No natural-film accuracy score or zero-false-alarm claim is justified.

## Unresolved and missed cases

None.

## Scope and reproducibility

Boundary: all original smoke cases plus luminance regime, leading spacing, red chroma and quadrant/glitch cases at 24/25/30/50/60 fps. Shapes: seeded S1 primitive variations. Truth is calculated from raw pre-codec samples by an independent offline reversal/window oracle; codec/analysis mismatches remain visible in scores. Original S1 ground truth is unchanged. Local/Kids truth uses their own product policies. Exact red chromaticity threshold remains covered by numeric unit tests, because 8-bit encoding cannot represent arbitrary u′v′.

Realistic: five effects over moving licensed footage at the manifest timestamps, 90% effect / 10% source in display-code space. They test injected hazards against complex backgrounds; they are not a representative natural-content prevalence sample. Scene descriptors identify inspected reference frames, not scene-label truth.

First measured observations cached by code/manifest/tool/params hash; use --fresh-measurements to measure again. Accuracy is recomputed on every default run; --resume reuses matching completed evidence. Decoded samples are losslessly compressed and checksum-keyed; full films are streamed without mitigation.

Decoded samples are compressed to bound disk use. Accuracy and timing observations are cached with source checksum and provenance. A repeated run regenerates byte-identical JSON and Markdown. generated_at in internal evaluation tracks is fixed to 2000-01-01 UTC; evaluation never publishes player tracks.

## Oracle source validation

The initial S4 oracle applied the HDR relative criterion to SDR high-dark states. Re-reading ITU-R BT.1702-3 Annex 1 Guideline 1 confirmed the SDR predicate: darker state below 160 cd/m² and difference at least 20 cd/m². Explicit 159/160/170 tests validate this distinction. The initial apparent misses are retained in [the correction audit](audits/sdr_oracle_correction.json). Every source clip, seed, randomized parameter, original S1 truth and production detector is preserved.

## Environment

```json
{
  "cpu_model": "Apple M1",
  "engine_version": "0.1.0",
  "ffmpeg": "ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers",
  "git_sha": "f30e7fc051147d454299a3333ef4c48e871fdd2b",
  "machine": "arm64",
  "memory_bytes": 8589934592,
  "params_hash": {
    "broadcast": "70dcc50ff260aa1abcb1137f7ca022293f27dbcdc6c694c49b1c3ed79455de6a",
    "kids": "eba16e78fcd87c00137e0d37641526314d2d4fe80aad5bbf6f54add615054832",
    "local": "14b825f91e0477aeabe01a0491ec83ce00d1b4096a43c5d582d5895ca4490538"
  },
  "platform": "macOS-26.3-arm64-arm-64bit",
  "python": "3.12.11"
}
```

Provenance:

```json
{
  "code_sha256": "c54447243779ad457991d7d5698e1ecd8a7ffe29f6902518e4283fee1cef6b88",
  "control_review_sha256": "c05d53262c47670fc0477b1ad77db35b4e565227a312b6ba3e3b5bd5e0f3fa07",
  "cpu_model": "Apple M1",
  "ffmpeg": "ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers",
  "machine": "arm64",
  "manifest_sha256": "10206c1b910c59032a19a7bafb0561289aba2ede50dc7603302784a018505862",
  "memory_bytes": 8589934592,
  "params_hash": {
    "broadcast": "70dcc50ff260aa1abcb1137f7ca022293f27dbcdc6c694c49b1c3ed79455de6a",
    "kids": "eba16e78fcd87c00137e0d37641526314d2d4fe80aad5bbf6f54add615054832",
    "local": "14b825f91e0477aeabe01a0491ec83ce00d1b4096a43c5d582d5895ca4490538"
  },
  "platform": "macOS-26.3-arm64-arm-64bit",
  "python": "3.12.11"
}
```

## Control exclusions and review

Tears of Steel originals lack required BT.709 tags and are not clean controls. The zero-fail expectation on the retained control is reported honestly; independent review of its flags is outstanding, so the clean-control acceptance claim remains open.

## PEAT cross-check

not run: no Windows PEAT environment available
