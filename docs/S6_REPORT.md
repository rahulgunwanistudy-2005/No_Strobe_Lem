# S6 — Vega viewing experience

Executed the supplied project bible and S6 prompt on Lane A, on 2026-10-06
IST. The user's explicit instruction authorizes systematic commits without
attribution trailers, overriding the bible's manual-commit default. S7/AWS,
Lane B and physical-TV validation were not started.

## Built

- Validated catalog with relative/HTTPS asset contracts, posters, duration,
  active-profile hazard count, visible D-pad focus and catalog retry.
- Broadcast/Local/Kids profile selection, automatic Kids household and warning
  preference, persisted using Amazon's SDK 0.24 AsyncStorage extension.
  The exact disclaimer and CC-BY attribution are D-pad reachable.
- Protected title-selection autoplay waits for verification, native media
  readiness, surface attachment and veil priming. Chrome hides after four
  seconds while playing and returns on remote input. Pause remains visible.
- Accessible hazard chip starts three seconds before cue support; OK skips
  past the complete cue tail, including overlapping cues. The scrubber maps
  red veils, amber warnings and striped unresolved intervals, and supports
  trapped left/right ten-second seeking with a visible focus border.
- Profile requests stage until a render frame, retain the previous verified
  track during fetch, and ignore stale responses. Source/position remain intact.
  The new scheduler is primed behind a brief shield; a failure pauses and blocks.
- Missing sidecars stay paused until an explicit unprotected choice; the
  persistent banner remains and that choice does not autoplay. Kids prefers
  “Keep paused.” Invalid/failing/unresolved tracks refuse playback. Native
  media failures and network failures offer retry.

The unresolved UI mapping is implemented, but the bible's canonical
`verifier.passes` refusal takes precedence over playing an unresolved sidecar.
No reader gate was weakened. Required FAIL events and all Kids events must be
covered by a positive veil even if a sidecar asserts `passes=true`.

## Verification

47 TV tests in nine suites pass, including chip boundaries, tick geometry,
overlapping skips, profile races, household settings, serialized writes,
verification refusal, missing-track consent, autoplay/readiness, guarded seeks
and native animation initialization. TypeScript, ESLint, generated-contract
checks, Python tool lint/format and copy audit pass. Engine implementation and
S5 measured model/tolerance are unchanged; the full historical S4 evaluation
was not rerun for this UX work.

All three architectures (aarch64, armv7, x86_64) build in Debug and Release.
The inspected aarch64 Release contains only demo media and no calibration
module/control labels; Debug adds sync/compositing media. Release package hashes
and inventories are in [the build receipt](evidence/s6/build-receipt.json).
No raw-playback toggle exists in the product UI.

Actual rendered VVD screenshots establish catalog → verified playback →
focused chip → skip to 8 seconds → settings → Local at the retained 8-second
position → back. A scrubber left seek returns to 0 and keeps its focus ring.
Kids shows two softened warnings and actual video with its veil. Settings
Kids/Off survive termination and relaunch without reinstall or emulator reboot.
The disclaimer and attribution are fully readable. Missing, explicit
unprotected-paused, failed verification, native media failure and catalog
retry/recovery were exercised with temporarily altered local server metadata;
all original fixture bytes were restored. See [evidence](evidence/s6/README.md)
and [persistence receipt](evidence/s6/persistence-receipt.json).

The demo source contains zero FAIL events. Broadcast/Local's gentle cue is
illustrative. Kids covers both warnings using a whole-excerpt alpha 0.10,
gray 0.25 veil, numerically checked with warning rejection at every measured
−0.268875/0/+0.268875-second offset. This is a reproducible demo recipe,
not a minimum-distortion solver result. [Numerical receipt](evidence/s6/kids_demo_verification.json).

## Performance and limits

Measured with Vega Perf CLI 0.24.0 / native Perfetto on VVD SDK 0.24.12112,
firmware OS 1.2 TV Ship/102282480, Apple M1 / 8 GiB. Appium 2.2.2 and Vega
JSON-RPC driver 3.30.0 are isolated in ignored local test directories.

Three final playback iterations yield 18.4–19.6 fps for the 24-fps excerpt,
76.7–81.7% video fluidity, and 923.4–1376.4 ms from Select release to first
video frame. Consecutive video drops remain nonzero. The **zero-drop target is
not met**, so S6 is not represented as passing every performance objective.
The native UI dropped-frame counters also contain nonzero values during this
playback trace; no causal attribution of every drop to rAF is established.

A separate focus scenario opens Settings and sends twelve directional moves
per iteration. All three runs report 100% UI/granular fluidity and zero 3+/5+
consecutive-drop events. Its 39 last-input-to-frame samples span 8–129 ms
(median 17, mean 25). The same report's first-input-to-frame metric spans
39–1191 ms (mean 548.2); both are preserved, so this is not a claim that every
end-to-end input latency is below 129 ms. Title-opening last-input latency is
245–265 ms and includes verification/player setup. [Final performance receipt](evidence/s6/performance-final.json),
[video report](evidence/s6/video-report.json), [focus report](evidence/s6/focus-report.json).
The default video validator checks that metrics are present (`!= -1`), not
that drops are zero. CLI success therefore does not close this gate.

The final three app-first-frame measurements are 362.503, 201.037 and
789.391 ms. First app frame and first video frame are separate measurements. Fully-drawn
markers remain absent in the launch measurements, so no complete launch KPI
pass is asserted. Retained values and provenance are in `S6_VALIDATION.json`.
No physical-TV performance claim is made. S7 remains unstarted.

Single UI screenshots are not timing calibration captures. Paused native seeks
can retain a previous/preroll image until Play; the player primes the target
clock and veil under a black shield before resuming. The S5 calibrated
simulation is retained; it is not a medical guarantee or validation of other
SDK/display combinations. The catalog needs its configured local server and
VDA reverse mapping; no cloud deployment is implied.

## Review findings resolved

Native focus checks led to horizontal scrubber trapping and keeping its node
focusable during guarded seeks. Settings attribution now resets scroll position,
and catalog cards fit the TV viewport with complete focus borders. Native
restart testing found the legacy core storage API lost settings, despite the
older reference endorsing it; migration to the current SDK library passed.

The clock's UI updates unnecessarily re-rendered native video/veil components;
memoization removes those renders. Exact unchanged opacity targets are cached.
A delayed zero-duration native initialization could overwrite a constant cue
with opacity 1; wait for native completion before scheduling exact targets,
and require that priming before autoplay. Device Kids playback and an ordering
regression confirm this fix.

Official guidance consulted through Builder Tools MCP:
[RN 0.83 AsyncStorage](https://developer.amazon.com/docs/react-native-vega/0.83/asyncstorage),
[SDK 0.24 storage library](https://developer.amazon.com/docs/vega-api/0.24/react-native-async-storage.html),
[TV focus guide](https://developer.amazon.com/docs/vega-api/0.24/tvfocusguideview.html),
[TVEventHandler](https://developer.amazon.com/docs/react-native-vega/0.83/tvEventHandler.html),
and the curated performance/Appium workflow documents. The SDK storage guide
was followed after actual native restart evidence contradicted the legacy
stopgap recommendation.
