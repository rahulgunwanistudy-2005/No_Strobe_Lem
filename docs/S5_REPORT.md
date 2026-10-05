# Session 5 — Vega player and calibration infrastructure

2026-10-05. Lane A, macOS 26.3 arm64 / Apple M1, 8 GiB RAM.
**Implementation and numerical/build checks pass; S5 acceptance is incomplete.**
The remaining gates require real rendered-device recordings and visual QA.
No sync/compositing measurement has been fabricated or substituted with a
unit-test value. `sync_calibration.json` and `compositing_calibration.json`
are intentionally absent. Engine tolerance remains the simulated default
±0.15 s, and the existing blend model remains unchanged.

## Delivered

- Current CLI helloWorld template, strict TypeScript, RN 0.83.0 / React 19.2.0,
  Kepler 4.0.1 and W3C Media 2.3.2. SDK/VVD 0.24.12112 / CLI 1.4.2.
  Dependency lockfiles are committed. The SDK's own wrapper uses Node 22.11.0
  and warns about Kepler's >=22.14.0 requirement; the host uses Node 24.19.0.
- One W3C player, initialized before source/surface assignment, isolated native
  imports, typed errors, idempotent cleanup and initialization/unmount race
  handling. Required player-session and system audio services are declared.
- Injected monotonic media clock: interpolation, pause/buffer/end hold,
  seeking, rate changes and large drift correction. Exact Python-compatible
  scheduler, including overlapping-cue tie breaks, ramp support and final-frame
  hold. Shared fixture has 500 samples and explicit seek/end cases.
- Absolute gray veil with per-frame scheduler targets and native-driven Animated
  opacity. Independent black shield covers loading/error/seek states. Native
  animation did not produce an unsupported-driver error; rendered opacity and
  compositing have not been visually or numerically measured. No unsupported
  fallback claim is made.
- Canonical JSON loading with generated standalone Ajv validation, source/content
  binding, unique IDs/reference/timing checks and refusal of failing/unresolved
  verifier results. WebVTT remains a portability-test reader. Generated types,
  schema and validator all have drift checks.
- Single CC-BY Big Buck Bunny demonstration, explicit Play and D-pad controls,
  fail-closed startup/seek behavior and required viewing-aid disclaimer. The
  12-second source excerpt and gentle illustrative overlay pass all profiles;
  it is not presented as a hazardous-source mitigation demonstration.
- Separate Debug-only sync/compositing lab, stimuli and bounded recording
  analyzers. Instant cues are nonproduction descriptors, not forged passing
  HazardTracks. Release packaging starts with clean generated staging so
  previously copied Debug raw assets cannot leak into Release.

## Verification

Machine-readable checks and package hashes are in `S5_VALIDATION.json`;
minimal actual event excerpts and package listings are in `evidence/s5/`.

- Engine full suite: **408 passed**, 446.77 s. After the final measurement-model
  refinement, all six calibration/conformance tests passed again. These use
  synthetic unit oracles explicitly distinguished from device evidence.
- TV: **30 tests / 7 suites passed**. Includes all 500 shared timeline samples
  within 1e-6, clock transitions/drift, native lifecycle races, malformed and
  failing tracks, WebVTT round trip, generated-output drift, import boundaries,
  calibration exclusion and covered/refused startup for verifier failure.
- TypeScript, eslint, root generated-contract checks, Python ruff check/format
  and strict mypy pass (56 source files). Release and Debug build on all three
  SDK architectures; package contents confirm only demo.mp4 in Release and
  demo/sync/compositing MP4 files in Debug. Project doctor reports all critical
  checks pass, with one scoped eslint plugin package-mapping warning.
- Real VVD Release playback: initialized surface and local source, duration
  12,000 ms, loadedmetadata/canplay; remote Enter emitted play/playing,
  advancing timeupdate events and ended after the excerpt. Pause and seeked
  were also observed through remote controls. App lifecycle reports VISIBLE.
  These logs establish native playback, not visual-layout or pixel correctness.
- Encoded sync and compositing stimuli: zero FAIL and zero WARN events on
  Broadcast, Local and Kids. Source hashes and detection preflight are retained
  in `s5_calibration_status.json`. Sync patch is 64×32 on 640×360, one source
  frame, every two seconds; digits/counter are low contrast. Composite ramp is
  static, with nine slow alpha/gray plateaus.
- Fresh saved-track audit: `engine/eval/s5_verification.json`, 325 cases / 975
  profiles, identical events, FN=FP=0 and all saved veils reverified at
  −0.15/0/+0.15 s, zero residuals/unresolved segments. This reruns detection and
  verification on retained exact decoded samples. It does not claim fresh
  solving, a new performance benchmark or measured device tolerance. Original
  S4 submission reports remain intact and correctly say simulation tolerance.

## Remaining gates and reproduced blockers

The host recorder (`ffmpeg` AVFoundation, screen device 1, requested 60 fps)
receives no frames; a bounded retry after restarting VVD also timed out.
Computer-use inspection could not obtain a Finder window. Device screenshooter
reported buffer permission failure and stalled; QMP screendump returned an
entirely black framebuffer. Device display-capture attempts did not produce
a valid stream. The desktop may be unavailable/locked, but that is not proven.
The user was asked to make it available; no answer or successful capture was
received. Empty/black outputs were rejected as evidence.

Therefore these are still open:

1. Visually inspect actual video/overlay/controls, including seek and background
   behavior, and confirm native Animated affects the rendered surface.
2. Capture >=60 fps sync runs for steady, seek and pause/resume; combine the
   measured offsets and apply the prescribed tolerance after outlier review.
3. Capture the compositing ramp, fit all nine cases and test RGB and limited-Y
   error separately. If error exceeds two codes, implement the measured model.
4. Rerun S3/S4 with the measured parameters and update RESULTS.md. No earlier
   default-tolerance audit can satisfy this requirement.

Commands and recording/crop requirements are in `tv/README.md`. Calibration
reports must retain actual timestamps, source/capture checksums and all
scenarios. The analyzer refuses missing edges/counters, bad baseline, low fps
and observed sync outliers beyond the derived bound.

## Sources and dependency limits

The [Amazon reference sample license](https://github.com/AmazonAppDev/vega-video-sample/blob/main/LICENSE)
was checked: MIT No Attribution. Only API/lifecycle patterns were used; no
sample file was copied. The CLI generated this app. The Blender excerpt keeps
[CC-BY-3.0 attribution](https://peach.blender.org/about/).
Amazon Builder Tools MCP supplied the media implementation workflow,
initialization/surface/API documentation, compatibility guidance and manifest
requirements. Actual logs revealed missing service declarations. Official
[local URI guidance](https://community.amazondeveloper.com/t/proper-uri-handling-for-local-assets-in-kepler-toastkepler-and-w3c-media-video/27642)
resolved HTTP media rejection through `/pkg/assets/raw/`; no TLS check was
weakened. See `FRICTION_LOG.md` and `PRODUCT_FEEDBACK.md`.

The template dependency graph retains npm audit findings documented in product
feedback; framework dependencies were not force-upgraded across SDK mappings.
AWS, S6 work and external publication are outside this session. User-authorized
commits contain no attribution trailers or AI tags.
