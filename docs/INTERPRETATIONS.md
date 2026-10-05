# Standards and product interpretations

Verified 2026-10-04. Standards sources govern over shorthand in the build pack.

- [ITU-R BT.1702-3 (11/2023)](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf): Annex 2, Table 1, printed p.7 (PDF p.9), SDR column transcribed into the CSV. This is a table, not a fitted formula. The values match [-2 (10/2019), Table 1 p.6](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-2-201910-S!!PDF-E.pdf). Annex 2 Figure 3 notes give D=400 → 20.1 and D=863 →160.4 cd/m²; interpolation of rounded table entries is used. Codes below 64 and above 940 clamp to 0 and 200 cd/m². Monotonicity is strict within the reference range, nondecreasing in foot/headroom.
- BT.1702-3 Annex 1 Guideline 1 p.3 specifies the relative criterion above 160 for **HDR only**. S1 implements the continuous `max(20,Ldark/8)` boundary helper requested in the brief. S2 must distinguish this helper from the SDR detector's absolute rule and verify behavior against the source. No standards-exact detector is claimed in S1.
- The relative contrast criterion is strictly greater than 1/17 above the boundary; the low-luminance absolute criterion is ≥20. This distinction must be handled in S2, not hidden in `thr`.
- The source permits leading-edge spacing ≥360 ms in 50 Hz and ≥334 ms in 60 Hz environments. The brief's constant 0.36 s across frame rates is a conservative product interpretation. Profile params preserve that requested constant; frame rate alone does not establish display refresh rate.
- Counting >6 qualifying changes in a trailing `(t-1,t]` window, per-cell area, local 1/3-screen windows, Kids >4 and extended-area 25% are product decisions. Source guidance mentions extended sequences >5 s; the numeric extended-area and change-rate settings are not attributed to the standard.

## Color

[WCAG 2.2 flash-threshold Note 3](https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds) requires a saturated endpoint with R/(R+G+B) ≥0.8 and distance >0.2 in CIE 1976 u′v′. It says **to or from a saturated state**, so a transition between two saturated endpoints is not excluded. The brief's entering/leaving-only formulation is incomplete. Opposing transition pairing is deferred to S2.

WCAG's working-definition note does not explicitly specify the transfer function of the RGB symbols. The project chooses linear RGB for the ratio and XYZ computation. Web sRGB uses WCAG's documented 0.04045 linearization. Video rgb24 uses inverse [BT.709-6 §1.2](https://www.itu.int/rec/R-REC-BT.709-6-201506-I/en); BT.709 primaries/D65 are converted to XYZ using [W3C CSS Color 4 conversion matrices](https://www.w3.org/TR/css-color-4/#color-conversion-code). Black has ratio 0 and undefined chromaticity is represented as (0,0); this conservative black transition convention is a product choice. The display luminance table is separate from these source-color helpers.

## Contracts and scaffold

Pydantic models are frozen with the field names and list containers required by §9. Freezing prevents attribute reassignment, not mutation inside lists/dicts. Readers must revalidate incoming JSON. Unknown fields are ignored. `generated_at` must be aware and is normalized to UTC. Veil times may be negative near the start of media; app clipping belongs to S5. `TrackStats` constrains fractions and counts.

S1 asks for only a TV README, whereas the bible places generated types inside TV. In S1 the generated contract was temporarily `spec/generated/hazardtrack.ts`; S5 moved it into `tv/src/types/` and added a standalone runtime validator. Schema and TypeScript drift checks run in tests/CI. Unimplemented later-stage modules fail explicitly with `NotImplementedError`.

Synthetic truth describes sampled raw primitives under the Broadcast product interpretation, independently of the future detector. It records quantized luma pairs, not requested ideal values alone. Lossy H.264 can alter spatial boundaries/color: S2/S4 must measure this rather than relabel ground truth to fit detection. Smoke clips are not the full S4 evaluation suite.

## Decode resolution and synthesis fidelity

The initial 320×180 grid failed the hard-edge spatial gate, so S1 raises both
luma and RGB decode defaults to 640×360 and averages 4×4 in linear light to
160×90 cells. The gate tests the 640×360 synthetic inputs; higher-resolution
source content needs renewed spatial-error evaluation in S2/S4.

Synth retains CRF 10 and additionally disables x264 psychovisual optimization
and adaptive quantization, with maximum QP 6. The cap is an encoding-quality
choice to preserve analytic test stimuli (not a hazard threshold). Matching
input/output BT.709 and range tags prevents an implicit color conversion.
Explicit x264 VUI tags preserve transfer/primaries metadata across encoders.

## S2 detection decisions

Re-read BT.1702-3 Annex 1 Guideline 1 (printed p.3), Ofcom Section 2
Guidance Notes Issue Twelve Annex 1 §§2,3,3.1.1 (printed p.18), and WCAG 2.2
flash-threshold Notes 2/3 on 2026-10-04. Source wording overrides the brief.

- SDR luma changes require darker luminance <160 cd/m² and delta ≥20 cd/m².
  The relative helper is retained for continuity tests/future HDR; SDR events
  never use it or report a relative regime.
- Zigzag threshold crossings in the same direction are not opposing changes.
  Rate counting coalesces those crossings and pairs alternating directions.
  The >6-change product reading includes a pending leading change only after
  a dense sequence of opposing flashes is established, preserving the S1
  independent sampled truth. A first flash is included when its successor is
  close enough; flashes at ≥0.36 s leading spacing are excluded from rate
  counts, but included in extended-flashing counts.
- The 0.36 s spacing remains a conservative display-environment assumption,
  not a rule inferred from source fps. Windows are (t-1,t], with a 1e-9 s
  tolerance solely for floating-point/PTS equality, not a relaxed threshold.
- Warning proximity requires both spatial and temporal evidence: at least
  80% of both limits, without a fail on that frame. Extended flashing uses
  unfiltered opposing changes (≥3/s), area >25%, continuously for >5 s;
  only warnings are emitted. Kids can warn/fail on isolated three flashes
  under its intentionally stricter product policy; the broadcast isolated
  ≤3-flash guarantee cannot also hold for Kids' >4-change limit.
- Adding isolated flashes *inside an existing burst* can exceed the rate
  threshold; the requested unrestricted property is mathematically false.
  Test isolated bursts separated from other flashes by more than one second.
- Before the first qualified change, luma follows both extrema and red widens
  a pair of observed color endpoints. Initial mid-level samples cannot mask
  qualifying two-state excursions. Once initialized, extrema follow direction.
- RGB cells are averaged after BT.709 inverse transfer, then classified in
  linear RGB. Opposing red transitions use the sign of the dominant u′v′
  displacement component; same-direction chromatic ramps are coalesced.
  Either endpoint can be saturated red, including two saturated endpoints.
  This pairing method is a product interpretation, not ISO certification.
- All-profile RGB analysis refuses unspecified/non-BT.709 transfer, primaries
  or matrix metadata rather than apply the wrong color model. S1 luma-only
  reading retains its earlier transfer scope.
- Per-cell threshold history retains the fixed 64-entry timestamp ring. Flash
  rate histories additionally batch cells by shared frame PTS to reduce memory
  traffic; count equivalence, retroactive insertion and expiry are tested.
  Capacity overflow raises an error rather than truncate evidence.
- Kids interval timing uses an independent >4-change oracle. Its earlier
  onset cannot be compared directly to S1 Broadcast >6-change intervals.
- Detection-only JSON is an unverified event report, never a HazardTrack.
  Full analyze/publishing remains gated on the S3 verifier.

## S3 mitigation and publication

- Historical S3 blending followed the build pack literally: numerical limited
  Y codes were divided by 255; gray used the same normalized code in Y and
  full-range RGB. This was not a measured device fit; S5 supersedes it with the measured
  range conversion described below.
- Cache raw 640×360 pre-average Y/RGB bytes in source-SHA-keyed `.npy` shards.
  Caching only average luminance and reversing the transfer would lose spatial
  information and understate simulation error. Shards preserve VFR timestamps,
  bound memory, and require about 0.88 MiB/frame of disk. Ignored caches can be
  removed at any time. Cache format/resolution are versioned in the key.
- Exactly identical rows/columns across a verification interval may be reduced
  before detection; area fractions and one-third windows remain identical under
  this replication. No approximate spatial subsampling is introduced.
- Local candidate checks include 1.5 s beyond ramp supports on either side.
  Candidate checks stop on their first observed failure; final full-file checks
  collect all failures at every offset. No-cue offsets are identical, so one
  full detector pass establishes all of them.
- Search every gray independently along increasing 0.02 alpha steps, including
  max_alpha. Distortion increases monotonically with alpha at fixed gray under
  the monotone table, so the first passing grid value is that gray's minimum
  grid distortion even if pass/fail is nonmonotone. Refine its preceding bracket
  to <=0.005, then compare actual active-support distortion across grays; ties
  choose lower alpha, then gray. This is a finite-grid result, not a continuous
  global-optimality proof.
- Kids warning targets must disappear in local candidate checks; a zero-alpha
  'pass' that merely leaves a warning intact does not implement veil_warn.
  The final publication criterion remains zero fail events, plus no unresolved
  segments. Broadcast/Local warnings alone receive no veil.
- JSON extends the 1.0 object with unresolved reasons and mean luminance cost;
  defaults preserve old fixtures. WebVTT stores event provenance in a separate
  NOTE, leaving its metadata NOTE exactly without events/veils. This permits
  complete round trips and validation of covers references.
- Reports re-run luma/red counters in each event context, selecting the cells
  whose peak qualifying-change count is maximal during the event interval.
  Before/after luminance traces use that same group. Extended events use raw
  opposing-change counts. Neither source frames nor video are embedded.
- Extended-warning candidates retain `extended_duration_s + 1.5` seconds of
  pre-context, rather than only 1.5. Resetting a >5 s persistence counter inside
  a shorter window would hide the very warning Kids is supposed to mitigate.
  Other candidates retain the requested 1.5 s context on both sides.
- A seven-second 2 Hz full-frame clip exercises Kids' extended-warning policy.
  It has no fail events, but the fixed lead/ramp padding cannot clear the
  one-second raw-change window before the >5 s warning is emitted at the late
  sync offset. This case must be marked unresolved even when the final
  fail-only verifier passes. Its test asserts refusal and an actual residual
  extended warning; the initial expectation of guaranteed suppression was not
  supported by the timing bounds. No source truth or detector threshold changes.

## S4 evaluation decisions

- `eval/manifest.yaml` uses the JSON subset of YAML 1.2, keeping manifest
  parsing strict and avoiding another runtime dependency.
- Truth enumerates raw pre-codec cell histories independently of production
  detectors. It uses the documented display model and profile rules. The
  original S1 truth files and generator are preserved. 8-bit chroma pairs
  bracket 0.2; exact equality remains a numeric boundary test.
- Timing is a recorded observation, not a deterministic algorithm output.
  Default eval reruns accuracy; it retains the first timing per code/manifest/
  tool/parameters/source fingerprint. `--fresh-measurements` replaces timing;
  `--resume` is an explicit recovery mode reusing completed evidence.
- Full unmodified films are source-detection controls, outside the binary
  confusion matrix until their flags have independently reviewed truth.
  Mitigation metrics cover every synthetic/composite profile track. Clean-film
  full mitigation is outside this accuracy control, and is not scored as passed.
- Big Buck Bunny is the full-film clean control. The official Tears of Steel
  720p and ToS-4k-1920 MOVs and Sintel trailer omit transfer/primaries/matrix
  metadata. They cannot be clean controls under the existing strict BT.709
  reader; no input check was relaxed. Tears of Steel is used only as a background
  for explicitly encoded BT.709 composites; ffmpeg's HD-source RGB conversion
  is an assumption for that artistic background, not a measured source transfer.
- Composite effects occupy 90% of the RGB code blend, retaining 10% moving
  source detail. These stress the verifier and are not a prevalence study.
- Historical S4 used a simulated ±150 ms sync tolerance. S5 replaces it with
  the measured ±268.875 ms bound described below.

Static source-frame review corrected the real-scene selections before composite
execution: the group scene at 450 s, street at 250 s, and dark display-lit lab at
350 s in Tears of Steel. This is a staged club-like strobe test, not a claim that
the film depicts a club. Boundary/shape truth was not changed to fit detections.
Big Buck Bunny's six Broadcast flag contexts were reviewed from isolated stills:
rapid character motion, high-contrast foliage, and animated/scrolling credits.
They are candidate motion/text false alarms, not adjudicated false alarms or
confirmed violations; `eval/control_review.json` records that distinction.

S4 oracle source correction: the first expanded run exposed seven apparent
misses on high-dark camera-burst cases. Re-reading BT.1702-3 Annex 1 Guideline 1
(printed p.3) confirmed the already recorded S2 correction: ≥160 relative
contrast applies to HDR only. The new oracle had mistakenly used the generic
HDR-capable helper's predicate. The erroneous observations remain unchanged in
`engine/eval/audits/sdr_oracle_correction.json`. The SDR oracle is corrected from
the source, with explicit 159/160/170 tests. No production detector, source clip,
seed, randomized parameters, original S1 truth, or acceptance gate is changed.

## Detection performance follow-up

The offline Python/NumPy architecture, all three profiles, source decoding,
160×90 spatial grid, thresholds and publication gate are unchanged. State
updates and summed-area scans now use single-core Numba kernels within that
engine. This replaces the brief's per-frame NumPy implementation detail to
meet the user's explicit performance request. There are no Python loops over
cells, worker pools, GPU kernels or approximate spatial reductions. Every
kernel explicitly disables `parallel` and `fastmath`; the original NumPy
BT.709 matrix multiplication is retained to preserve its rounding behavior.

Numba 0.67.0 and llvmlite 0.49.0 are pinned in uv.lock; NumPy remains 2.5.3.
The [Numba compatibility table](https://numba.readthedocs.io/en/latest/user/installing.html#version-support-information)
supports Python 3.12 and NumPy 2.5 in that release. Strict arithmetic and compiled
loops follow the [Numba performance documentation](https://numba.readthedocs.io/en/stable/user/performance-tips.html).
Compilation and loading cached kernels have startup costs. Cold and warm
whole-film measurements account for kernel work inside detection, including
first-call compilation; decoding/cell conversion and full mitigation are
reported separately.

Standalone ChangeDetector retains its crossing timestamp ring. LumaFlashDetector
skips that unused duplicate history because FlashCounter already retains the
opposing-edge histories used for rate and extended detection. Retroactive
history insertion touches only selected cells while retaining the same masks,
expiration, 64-change capacity and 1024 distinct-timestamp limit. Profile area
calculations share only identical per-frame count thresholds and spatial rules.

A frozen pre-optimization reference from dd980e5 checks exact state, counters
and timestamp masks at all five supported frame rates, irregular timestamps,
strict red and SDR boundaries, and the full grid. New compiled counter inputs
also reject mismatched shapes before accessing native array memory.

## S5 measured Vega timing and compositing

The requested host screen recorder produced no frames on this host. The
SDK-bundled authenticated `EmulatorController.getScreenshot` API instead
captures the rendered VVD application surface, including native video and
the RN veil. The four accepted recordings exceed 60 actual samples/s and
preserve original SDK timestamps in lossless FFV1; no interpolation or
nominal-rate retiming is used. This substitutes the acquisition API, not
synthetic frames, for the requested OS recording. Exact provenance and
rejected attempts are retained in the S5 report.

For `max(p95 * 1.5, 0.1)`, p95 is the largest absolute-offset p95 across
steady, seek and pause/resume scenarios. This conservative interpretation
prevents extra steady onsets from diluting the slower seek distribution.
Measured p95 is 0.17925 s, yielding 0.268875 s; the 0.223 s observed maximum
fits the bound. An already-veiled pulse exactly at the seek destination has
coverage pixels but no new onset to time. It is recorded separately without
inventing an offset; eight other seek onsets establish the timing distribution.

The native view rounds its RGB gray to an integer display code. The measured
model therefore uses `q = floor(gray * 255 + 0.5) / 255` for RGB, and
`(16 + 219*q) / 255` for decoded limited-range BT.709 Y. Alpha blending stays
in code space, before transfer and spatial averaging. All nine requested
alpha/gray combinations cover input display codes 16…235, with the corresponding
actual decoded limited Y samples retained explicitly. The former model's
12.535-code Y error is preserved; the corrected maximum is 0.953 Y codes and
0.750 RGB codes. Engine parameter version 1.1 and calibration hashes invalidate
old evidence. These are VVD/backend measurements, not a physical Fire TV fit.

## S6 viewer behavior

The user's request to commit takes precedence over §22.2's manual-commit
baseline. S6 uses S1's Lane A and retains S5's measured playback semantics.

A missing sidecar is distinct from failed verification: the former offers an
explicit unprotected-playback choice and persistent banner, with playback
paused by default for every profile (including Kids). The latter always
refuses playback. S6's missing-track fallback is never automatic, because
bible §14 forbids default unmitigated playback. Unresolved ticks and chips are
mapped for diagnostic/future catalogs; unresolved tracks still fail the reader.

Chip lookahead begins three seconds before the cue's visible ramp begins;
skipping goes beyond its full tail/ramp, extending through overlapping cues.
Warning-only events appear in amber without a skip chip. Unresolved lookahead
ignores the warning toggle. This presentation does not alter veil execution.

Changing a household to Kids selects and persists Kids automatically. Family
resets to Broadcast; Kids households cannot select a less strict profile.
Settings writes are serialized. A profile request keeps the previous verified
track while fetching; the latest successful response stages until a render
frame, then a shield covers native propagation of the new scheduler. No media
reload or seek occurs. Failed or mismatched profile requests pause and block.

Vega 0.83 documentation explicitly endorses core AsyncStorage as its interim
supported SQLite-backed implementation. Use only getItem/setItem with an
app-scoped key, behind the platform boundary; no additional storage package.
D-pad focus uses native navigation and visible borders. Input listeners do not
override native directional focus; scrubber horizontal trapping uses a focus
guide. Release has no raw-playback toggle or calibration route.

The S6 demo has no FAIL events, but Local/Kids detect warning candidates in
ordinary motion. Kids now uses a whole-excerpt illustrative veil, searched
on the profile's alpha grid at gray 0.25 and checked with reject_warnings=True
at every measured offset. It covers both warning ids. This is a demo recipe,
not a new production solver or minimum-distortion claim. Uncovered required
FAIL events (or any Kids events) are rejected by the TV reader even when a
sidecar carries a passes=true flag. Source detection and the S5 engine model
remain unchanged. The disclaimer is a focusable scroll destination so a
D-pad viewer can read the complete exact text.
