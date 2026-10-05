# Session 4 report — 2026-10-05

Scope: the supplied S4 evaluation session under the project bible and the
existing S1/S2 standards corrections. The user's explicit commit instruction
supersedes the manual-commit default. Commits contain no attribution trailers.
TV implementation, measured device synchronization/compositing and AWS remain
later-session work.

## Built

- `cd engine && uv run nostrobe eval` runs the manifest and writes
  `engine/eval/RESULTS.md` and `engine/eval/results.json`. These generated
  artifacts are the sole source of submission numbers.
- 120 boundary clips cover the original S1 smoke cases plus luminance-regime,
  spacing, red, area and glitch boundaries at 24/25/30/50/60 fps. Another 200
  seeded clips vary the existing ten S1 primitives; seed and every parameter
  remain fixed in the manifest/generator. Original S1 truth is unchanged.
- Five three-second effects are composited over moving excerpts from official
  Blender open movies. Downloads and ZIP extraction are checksum-pinned;
  official license snapshots and attribution are committed. The composites
  use 90% effect / 10% source in display-code space and explicit BT.709 tags.
  They test injected hazards, not natural-content prevalence.
- Independent pre-codec truth uses offline reversal pairing and time-window
  counts with each profile's area/rate rules. Encoding and analysis mismatches
  remain visible rather than being silently relabeled.
- All three profiles run detection, mitigation, whole-file verification and
  viewing-cost measurement on every synthetic/composite clip. Results include
  confusion counts, interval IoU distributions, unresolved reasons, costs,
  measured throughput and environment/source/parameter provenance.
- Lossless decoded-sample archives preserve original code values and timestamps
  while bounding temporary disk use. Default runs recompute accuracy and
  mitigation; provenance-bound first timing observations are retained for
  reproducible reporting. `--fresh-measurements` replaces timings; `--resume`
  reuses completed evidence after checking actual source bytes.
- The full unmodified Big Buck Bunny film is streamed as a detection control;
  all flags and static/numerical luminance traces are retained. It has no
  independently adjudicated truth and is excluded from confusion scores.

## Oracle source correction

The first S4 oracle incorrectly applied the HDR relative-change rule to SDR
states whose darker luminance was at least 160 cd/m². This created seven
apparent misses on three unchanged seeded camera-burst clips. Re-reading
ITU-R BT.1702-3 Annex 1 Guideline 1 confirmed that SDR uses a darker state
below 160 cd/m² and a change of at least 20 cd/m²; the relative rule above
that regime applies to HDR. The existing production detector was already
correct under the S1/S2 source interpretation.

The oracle was corrected from the published criterion, with explicit
159/160/170 regression checks. The original apparent-miss observations and
provenance remain in `engine/eval/audits/sdr_oracle_correction.json`. No source
clip, seed, randomized parameter, original S1 truth, production detector or
acceptance gate was changed to erase a disagreement.

## Verification

The final quality run passed 374 tests in 734.26 s, including the encoded
composite regression. Lint, formatting, strict types (50 source files),
schema/generated-TypeScript drift and TypeScript typechecking pass. Tests
include a positive flashing clip that needs veils:
two default evaluation runs invoke mitigation twice and produce identical
reports. A separate check rejects changed media during resume.

Both complete default runs passed. Their generated results contain zero
misses and false alarms against profile truth: Broadcast 96 must-fail / 229
must-pass cases; Local 108 / 217; Kids 142 / 183. All 975 profile tracks
re-verify at −150/0/+150 ms, including all 355 tracks containing veils;
zero segments are unresolved. Interval IoU median is 1.0 for every profile.
These figures come from `engine/eval/results.json`.

The 326 case files include one full-film control and 305 distinct source
checksums. Seeded variations can produce identical encoded content; the case
counts are not a claim of 326 independent media sources or a statistical
natural-content sample. The film trace was inspected as a static image.

Both runs executed `cd engine && uv run nostrobe eval`, recomputing accuracy
and mitigation without `--resume`. Both returned exit 0 with 978 outcomes.
`results.json` and `RESULTS.md` are byte-identical, with no excluded fields.
The command, provenance, exits and SHA-256 hashes are recorded in
`engine/eval/determinism.json`. The internal evaluation date is fixed and
first timing observations are retained under the documented provenance policy.

The first complete-suite attempt stopped at the first realistic composite:
output color flags alone did not preserve transfer/primaries metadata. Matching
raw-input tags and x264 VUI tags now follow the existing S1 encoder convention;
a real encoded-output regression checks strict metadata acceptance and decoded
RGB fidelity. Production input checks were not weakened.

`engine/eval/audits/composite_encoding_correction.json` records the failure and
input-cache reuse. All generator/oracle/decoder/manifest inputs were checked
against the prior revision, and every one of the 320 synthetic media hashes
was checked. Only truth and lossless decoded inputs were copied into the new
provenance directory; observations, timings and environment were not reused.
The corrected complete runs recompute all accuracy and mitigation results.
Synthetic decode timings therefore measure loading prepared sample archives;
realistic timings retain their first measured decode/analysis observations.

## Limits

- Tears of Steel's inspected official originals omit required source color
  metadata. The engine's strict input checks remain intact; it is used only
  as a background in generated tagged composites, not as an unmodified clean
  control. That background conversion is an assumption, not a measurement
  of the original transfer function.
- Static review of Big Buck Bunny's flagged contexts found high-contrast
  movement, foliage and credits. Cell luminance reversals can arise from
  motion; these remain candidate motion/text false alarms, not confirmed
  false alarms or confirmed broadcast violations. Local/Kids flags also
  remain unadjudicated. No zero-false-alarm natural-film claim is supported.
- Full analyze throughput covers synthetic/composite decode/cache handling,
  detection, solving and verification. The film is a detection-only control.
  Timing excludes media generation, truth calculation and report rendering;
  the host was not reserved for benchmarking.
- The S4 revision did not meet the earlier 20× detector-throughput target.
  Its generated report retains those historical detect/full-analyze timings,
  including slow realistic candidate searches. The subsequent
  [performance follow-up](PERFORMANCE.md) records passing cold/warm full-film
  detection measurements and a separate accuracy/verifier audit.
- Verification at −150/0/+150 ms uses the existing simulation tolerance. It
  does not establish measured device timing, compositing fidelity, clinical
  safety or standards certification. Failed tracks cannot be published.
- PEAT was not run: no Windows PEAT environment was available. Device and
  cloud measurements are not invented.
