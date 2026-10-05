# Session 5 — Vega playback and measured calibration

2026-10-05 UTC. Lane A, macOS 26.3 arm64 / Apple M1, 8 GiB RAM.
**Device, implementation, quality and S3 gates pass; the full S4 rerun is running.**
The initial capture blocker is resolved. Both calibration reports contain actual
rendered VVD measurements. The remaining acceptance step is the complete fresh
S4 evaluation, followed by final evidence review and commits.

## Measured device behavior

The SDK-bundled, authenticated `EmulatorController.getScreenshot` API captures
the actual VVD application surface. Host AVFoundation produced no frames;
QMP read a different, black framebuffer. The fallback uses the existing SDK
token only in memory on a loopback endpoint. It creates no interpolated frames,
frame duplication or nominal-rate retiming. Four accepted recordings contain
**11,070 actual rendered samples**. Lossless FFV1 preserves their frame count
and SDK timestamps within **0.5 ms**. Exact crops, rates, hashes and input
observations are in `evidence/s5/capture_provenance.json`; original PNGs,
recordings and per-frame timestamps remain in ignored `synth_out/s5/captures/`.

| Scenario | Actual average capture fps | Timed onsets | Median signed offset ms | Absolute p95 ms | Maximum absolute ms |
|---|---:|---:|---:|---:|---:|
| Steady | 134.358 | 11 | 108.000 | 132.500 | 143.000 |
| Seek | 62.246 | 8 | 72.000 | 179.250 | 223.000 |
| Pause/resume | 96.648 | 11 | 95.000 | 114.000 | 124.000 |

The seek counter jumps by 4.752 s. Its exact frame-240 pulse is already under
the full target veil: background 88 and patch 181 display codes. That flash is
retained as coverage evidence, without inventing a new onset offset. Eight
other flashes have measured onset offsets. Pause/resume includes a 4.329 s
interior-frame hold; startup/EOF holds cannot satisfy this gate.

`engine/eval/sync_calibration.json` retains every onset and the pooled p95.
For the verifier, **p95 is the largest per-scenario p95**, so adding steady
samples cannot dilute the slower seek distribution. This conservative
interpretation uses the prescribed `max(p95 * 1.5, 0.1)` formula:
**sync tolerance = 0.268875 s**. The observed 0.223 s maximum fits the bound.
The largest acquisition interval is about 40 ms and is reported separately.
Engine profiles cite the report and use parameter version **1.1**.

All nine alpha/gray combinations were measured over all **220 input display
codes 16…235**, with a baseline check before fitting. The descriptor also
retains actual decoded limited-range source Y codes. The original engine Y
model missed by **12.535 codes**, despite a good RGB fit. The corrected model
uses the player's rounded RGB gray `q = floor(gray*255 + 0.5)/255`:

- RGB target: `q`; blend `(1-alpha)*rgb + alpha*q`.
- Limited BT.709 Y target: `(16 + 219*q)/255`; blend in decoded Y code space.

`engine/eval/compositing_calibration.json` reports maximum errors of
**0.750 RGB codes / 0.953 Y codes**, both below the two-code gate. The original
error is retained per case and in `eval/audits/s5_original_compositing_model.json`.
All verifier cache paths use the same corrected model, including grouped
cells and distortion calculations. Independent range oracles cover all nine
combinations; zero-alpha source detection remains unchanged.

## Vega implementation and visual checks

- CLI-generated template; strict TypeScript; RN 0.83.0 / React 19.2.0,
  Kepler 4.0.1, W3C Media 2.3.2, SDK/VVD 0.24.12112, CLI 1.4.2.
- One W3C player, awaited initialization before source/surface assignment,
  typed errors, required services and idempotent cleanup. Vega imports are
  isolated in `player/` and checked by tests/lint.
- Injected monotonic clock and exact Python-compatible scheduler. Shared fixture
  has 500 samples, including overlap, seek and end cases, within 1e-6.
- Native-driven Animated opacity works above the native video surface, as
  established by the nine actual pixel plateaus. No JS fallback is needed
  on this SDK/device combination. A separate black shield covers loading,
  errors and seeking while the new clock/veil are primed.
- Canonical JSON uses generated types/schema/standalone Ajv validation,
  source/content binding and refusal of failing/unresolved verifier results.
  WebVTT remains a portability-test reader. Generated artifacts have drift gates.
- The checksum-pinned CC-BY Big Buck Bunny excerpt is reverified on all profiles
  at the measured tolerance, with and without its gentle illustrative cue.
  It demonstrates playback; it does not claim a source hazard was mitigated.
- Actual Release screenshots confirm video/veil, readable focus rings and
  controls, and the complete viewing-aid disclaimer. A deliberately failing
  verifier fixture keeps the video covered and controls disabled. The sidecar
  was restored byte-for-byte after this check. Background/foreground returns a
  covered/stopped player, and fresh restart works. See `evidence/s5/README.md`.
- Initial paused +10 s seek emitted seeking/seeked and remained covered while
  pending. Under concurrent evaluation it took about 4.8 s and retained a black
  preroll image until Play; playback then resumed at the requested target and
  ended after the remaining excerpt. This is not a seek-latency benchmark.
- Debug lab descriptors are separate, nonproduction calibration artifacts.
  Release starts with clean SDK staging and contains only demo media;
  Debug contains demo/sync/compositing. All six architecture/mode packages
  rebuilt successfully; hashes and actual inventories are retained.

## Verification

Machine-readable evidence is in `S5_VALIDATION.json` and `engine/eval/`.

- **421 engine tests passed**, 526.26 s; **30 TV tests / seven suites passed**.
  The current determinism regression recomputes encoded mitigation twice.
- Python lint/format/strict mypy, root/TV TypeScript, generated-contract drift
  and platform-import gates pass. The native-driver path remains the default.
- Both encoded calibration sources have zero FAIL/WARN events on Broadcast,
  Local and Kids using the current profiles. Source hashes and preflight are
  retained in `s5_calibration_status.json`.
- **Fresh S3 rerun: 80 encoded cases / 240 outcomes, all verified**, zero
  unresolved segments, FN=FP=0 on every profile. Broadcast must-pass cases
  receive no veils. `s5_smoke_verification.json` records fresh encoding,
  detection, solving and final whole-file verification; no saved tracks reused.
- **Fresh S4 rerun is running.** It regenerates independent truth and encoded
  cases, detects/solves/verifies all profiles at the measured tolerance and
  streams the full retained film control. Its final reports will replace the
  submission numbers only after the complete gate result is available.

The initial S5 saved-track audit at ±0.15 s remains historical evidence in
`s5_verification.json`. The original S4 two-run determinism proof also refers
to its historical simulated parameters. Neither is labeled as the new measured
rerun. Original source truth, standards corrections and historical evidence
remain preserved in Git. Natural-film accuracy/adjudication and PEAT retain
their earlier explicit limits; synthetic/composite scores exclude the
unadjudicated film control.

## Reproduction and limits

`tv/README.md` documents acquisition, native process reset, timestamp-preserving
encoding, crops and measurement commands. Reruns:

```sh
uv run --project engine python tools/verify_s5_smoke.py
uv run --project engine nostrobe eval --fresh-measurements
```

Every parameter change invalidates evidence through code/profile/source and
calibration checksums. Low-rate, obscured, stale-instance or overloaded
recordings were rejected and retained as diagnostics. Debug filters remove
three exact SDK/vendor notifications that covered calibration pixels; actual
warnings remain in device logs and playback errors remain visible.

These measurements apply to this VVD/SDK/display backend. Physical Fire TV,
other SDKs, AWS and S6 work are outside this session. The template dependency
audit findings and SDK Node-wrapper compatibility warning remain documented
in `PRODUCT_FEEDBACK.md`; no unsupported force-upgrade was performed.

## Sources

The [Amazon reference sample license](https://github.com/AmazonAppDev/vega-video-sample/blob/main/LICENSE)
was checked: MIT No Attribution. Only API patterns were used. The Blender
excerpt retains [CC-BY-3.0 attribution](https://peach.blender.org/about/).
Amazon Builder Tools MCP supplied media workflow/API/manifest guidance.
[Amazon's local URI guidance](https://community.amazondeveloper.com/t/proper-uri-handling-for-local-assets-in-kepler-toastkepler-and-w3c-media-video/27642)
resolved HTTP media rejection through `/pkg/assets/raw/`; TLS checks were not
weakened. [Amazon's VVD capture discussion](https://community.amazondeveloper.com/t/sdk-0-24-12112-vvd-gwsi-tool-screenshooter-writes-a-0-byte-png-or-hangs/29249)
and the SDK's bundled `emulator_controller.proto` informed the authenticated
capture fallback. Friction and product feedback record actual failures and fixes.
