# S4 evaluation results

Detection and verifier gate: **PASS**.

Headline numbers (these are the sole submission-number source):

- broadcast: **0 missed hazards** on 96 must-fail clips; 0 false alarms on 229 must-pass clips.
- local: **0 missed hazards** on 108 must-fail clips; 0 false alarms on 217 must-pass clips.
- kids: **0 missed hazards** on 142 must-fail clips; 0 false alarms on 183 must-pass clips.
- 975/975 profile tracks re-verify at −268.875, 0, +268.875 ms (measured VVD tolerance; see sync_calibration.json and compositing_calibration.json).
- 0 unresolved segments retained with reasons; publication refused for affected profile tracks.

VVD calibration: worst-scenario absolute p95 179.250 ms; maximum 223.000 ms. Measured RGB/model-Y maximum errors: 0.750/0.953 codes. Calibration file checksums are in provenance.

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
| broadcast | 325 / 325 | 0 | 0.278428 | 0.432571 | 16.789856 |
| local | 325 / 325 | 0 | 0.312563 | 0.430608 | 18.479293 |
| kids | 325 / 325 | 0 | 0.448651 | 0.458386 | 24.976024 |

## Throughput

All-profile shared passes. Full analyze includes decode/cache loading or packing and detection/solve/verification; it excludes generation, truth calculation and report rendering. Detect includes cell conversion for the synthetic/composite cache runs. Full-film detect below measures detector updates separately. Host was not reserved for benchmarking.

| Suite | Clips | Duration s | Detect × real-time | Full analyze × real-time |
|---|---:|---:|---:|---:|
| boundary | 120 | 350.000000 | 5.1778 | 0.3227 |
| shapes | 200 | 600.000000 | 4.6285 | 0.6273 |
| realistic | 5 | 15.000000 | 5.5316 | 0.0257 |
| clean | 1 | 596.458333 | 32.3924 | not run (detection control) |

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
  "git_sha": "c2372f23ba25430314748cfa02d005430761a501",
  "machine": "arm64",
  "memory_bytes": 8589934592,
  "params_hash": {
    "broadcast": "a9a3a0b32dc6adbc3ed56629267c79ad73363ffbca96999abcd9fe84ad5f3f94",
    "kids": "134f76ec2fe221ad3e34c239805112825d152f986a83517598307bf898f6ee94",
    "local": "d7a84ea89591a7758880e901cf24f0d83c10e4a5f2e0eb05dd7e7181b3290a1d"
  },
  "platform": "macOS-26.3-arm64-arm-64bit",
  "python": "3.12.11",
  "sync_tolerance_s": 0.26887499999999925
}
```

Provenance:

```json
{
  "code_sha256": "f34c34ce1d68ea31ef6f37d1f6e86d02bbc4cbf8ed90cb63bb27cfbcf6a1c5b4",
  "control_review_sha256": "c05d53262c47670fc0477b1ad77db35b4e565227a312b6ba3e3b5bd5e0f3fa07",
  "cpu_model": "Apple M1",
  "device_calibration": {
    "compositing_max_error_codes": 0.75,
    "compositing_sha256": "293dc4cf29f6d78f523e1297d685b9fb52115fcda64a2d00b32674b2ddc72515",
    "engine_y_max_error_codes": 0.9529411764706026,
    "sync_max_abs_s": 0.22299999999999986,
    "sync_p95_abs_s": 0.1792499999999995,
    "sync_sha256": "6a1e858f394fb33f1ad4a1d24a9e3836ace20f5006b5ff9e072532d2b9fee80c",
    "sync_tolerance_s": 0.26887499999999925
  },
  "ffmpeg": "ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers",
  "machine": "arm64",
  "manifest_sha256": "10206c1b910c59032a19a7bafb0561289aba2ede50dc7603302784a018505862",
  "memory_bytes": 8589934592,
  "params_hash": {
    "broadcast": "a9a3a0b32dc6adbc3ed56629267c79ad73363ffbca96999abcd9fe84ad5f3f94",
    "kids": "134f76ec2fe221ad3e34c239805112825d152f986a83517598307bf898f6ee94",
    "local": "d7a84ea89591a7758880e901cf24f0d83c10e4a5f2e0eb05dd7e7181b3290a1d"
  },
  "platform": "macOS-26.3-arm64-arm-64bit",
  "python": "3.12.11",
  "sync_tolerance_s": 0.26887499999999925
}
```

## Control exclusions and review

Tears of Steel originals lack required BT.709 tags and are not clean controls. The zero-fail expectation on the retained control is reported honestly; independent review of its flags is outstanding, so the clean-control acceptance claim remains open.

## PEAT cross-check

not run: no Windows PEAT environment available
