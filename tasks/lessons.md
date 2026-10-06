# Lessons

- User commit authorization takes precedence over the build pack's default manual-commit rule.
- Validate published source wording before implementing thresholds; product interpretations must be labeled separately.

- BT.1702-3 specifies the ≥160 relative rule for HDR; the brief's fixed leading-edge spacing is a product generalization, not the full published wording.
- Use integer frame indices for sampled one-second truth windows to avoid false extra changes at floating-point boundaries.
- Specify matching input/output color metadata as well as encoder VUI metadata; inspect ffprobe output rather than assuming flags worked.
- Spatial averaging must follow conversion to cd/m². The initial grid failed the hard-edge test; raised resolution and synthesis fidelity passed the unchanged <1 cd/m² gate.
- WCAG's red-threshold note leaves RGB transfer implicit. Document linearization as an interpretation and do not assume two saturated BT.709 colors can exceed a 0.2 chromaticity distance; independently check the chosen test colors.

- S2: a 0.34 s flash period does not itself imply >3 flashes/s; both temporal
  and area criteria are still required. Spacing eligibility and rate failure
  need separate boundary checks.
- Kids can fail isolated triples because its product limit is >4 changes;
  use per-profile truth and timing, not Broadcast truth relabeled for all profiles.
- Batched cell masks preserve per-cell temporal counts while avoiding redundant
  frame timestamp storage. Benchmark decode/cell conversion separately from
  detector time and report an unmet performance target honestly.
- Explicit BT.709 conversion requires explicit BT.709 source tags in S2;
  earlier luma-only support for other SDR transfer tags does not imply RGB support.
- Track both startup extrema before a direction is registered. A first sample
  inside a later qualifying range can otherwise hide all subsequent flashes.
  Red detection likewise needs observed startup color endpoints, not only the
  first RGB sample. Regression tests cover both luma directions and red at all fps.

- S3: blend original display-code samples before transferring/averaging into
  analysis cells. Inverting an average luminance loses subcell variation.
- S3: verifier success alone does not implement Kids' veil_warn policy; local
  solver candidates must suppress the selected warnings as well.
- S3: preserve event provenance separately in a WebVTT NOTE so complete round
  trips can validate cue covers without altering the metadata NOTE contract.
- S3: grouping byte-identical sample histories is exact only if the detector's
  counts expand back to the original spatial grid before every area decision.
- S3: segment context must include the detector's longest history. Extended
  warnings require >5 s of persistence; a 1.5 s reset can falsely accept a
  zero-alpha Kids candidate. Keep the longer prefix and test actual suppression.

- S4: validate the independent oracle against source-corrected rules as well as
  the original brief. Smoke-only agreement hid an HDR/SDR distinction because
  its high-dark amplitudes did not separate the two predicates. BT.1702-3 Annex 1
  Guideline 1 applies relative contrast at/above 160 cd/m² to HDR only. Preserve
  erroneous provisional observations as an audit, retain every clip/seed/gate,
  and add explicit 159/160/170 regime tests before rerunning evaluation.
- S4: every encoder needs a real encoded-output preflight before a long suite.
  The composite encoder omitted the matching input/codec VUI metadata already
  required by the S1 encoder. Output flags alone again lost transfer/primaries;
  preserve strict decoder refusal and test metadata plus decoded RGB fidelity.

- Performance: changing the shape of an otherwise equivalent matrix product
  can change its rounding. A transposed RGB-to-XYZ product differed by up to
  1.11e-16 on the 9x12 differential grid. Retain the original NumPy matrix
  multiplication; compile the following state work with fastmath disabled.
- Performance: profiling a quiet opening is insufficient. Measure every frame
  of the full film, all profiles, both detector CPU and wall time, and an empty
  JIT cache. Keep decoding/cell conversion and full mitigation costs separate.

- S5: inspect final package contents after switching Debug to Release. SDK raw
  asset staging can retain files removed from the source tree; clean generated
  Release staging before packaging calibration-sensitive assets.
- S5: full-range captured RGB and original limited-range Y are different code
  domains. A perfect RGB alpha blend can still disagree with the engine's Y
  simulation by more than two codes. Compare both using actual decoded source
  samples; change the production model only after real device measurement.
- S5: native media success and VISIBLE lifecycle state do not prove rendered
  overlay pixels or sync. Reject empty/black captures and keep calibration
  parameters explicitly unmeasured. Restore device port reverse after reboot.

## S5 measured continuation — 2026-10-05 UTC

- Captured RGB display codes and decoded limited BT.709 Y use different gray
  targets. Match the player's rounded RGB code, then convert its target to
  limited Y with the 16-code offset and 219-code span. A good RGB fit alone
  concealed a 12.535-code engine Y error. Share the corrected model across
  every verifier/distortion cache path and rerun solving after the change.
- Reinstall/launch can retain an existing native process and playback position.
  Explicitly terminate between calibration runs; use source counters to detect
  stale state, actual seeks and interior pause holds. EOF holds do not establish
  pause/resume. Never rename a steady recording to claim another scenario.
- A pulse at an already-veiled seek frame has no new onset to time. Keep its
  measured coverage pixels separately and require enough other timed onsets;
  do not invent a zero offset or silently drop an uncovered flash.
- Acquisition is part of the experiment. QMP/OS/native APIs may expose different
  buffers, debug notifications can obscure the pulse, and request overhead can
  perturb the emulator. Reject insufficient/obscured/overloaded records, retain
  diagnostics, record actual rates/intervals and preserve SDK timestamps. Use
  the worst scenario p95 so extra steady observations cannot dilute its bound.

- S6: the launcher can report VVD ready even though its process dies when
  its parent tool terminal closes. Keep a terminal alive, then independently
  check device discovery before using readiness as evidence.
- S6: TVEventHandler observes navigation but cannot override native focus.
  Keep the scrubber focusable during a guarded seek; disabling its focus
  eligibility moves focus to another control. Ignore input while seeking
  instead. Preserve actual screenshots and seeked events as evidence.
- S6: the Kepler Jest preset's BackHandler mock differs from its default
  runtime export. Mock that boundary without spreading the entire lazy
  platform export object (which eagerly invokes unrelated native getters).

- S6: Verify stored settings by terminating and relaunching the native process,
  with no intervening reinstall. The supported SDK AsyncStorage extension
  retained Kids/Off; the legacy core API did not on this VVD.
- S6: Await native Animated initialization completion before sending exact
  cached opacity targets. A delayed zero-duration initialization can overwrite
  a constant Kids cue. Regression tests cover ordering and repeated writes.
- S6: Memoize native surface/veil components against the chrome clock updates;
  stable props avoid unnecessary native surface renders. Performance traces
  must still establish actual drops; render optimization alone is not a pass.

- S7: ffmpeg's human-readable pts_time can round exact flash-window boundaries
  differently across releases. Decode integer PTS with the filter's rational
  time base, invalidate old decoded caches, and preserve independent truth.
- S7: an installed wheel's module path is not a product checkout root. Use the
  working directory for writable caches outside a source checkout; verify the
  actual CI-built wheel inside the read-only deployment image.
- S7: listing status objects alone does not serialize catalog publication.
  Read the old catalog ETag before listing, condition the write on that ETag,
  and relist after a competing write. Test the actual competing interleaving.
- S7: measure uncompressed image size rather than release archive size. A
  minimal static decoder build fits the budget; pin its source, binary checksum
  and provenance so separate SAM builders avoid repeating slow compilation.

- S8: synchronous refs serialize same-turn seek input before React state updates.
  Cover native dispatch/completion with a separate flag; media errors cancel
  queued dispatch and any deferred resume. Verify the regression fails without
  its guard, rather than merely mirroring an implementation branch.
- S8: a timed-out Docker client can leave its container running. Record a
  per-check container id and clean up only that owned container in finally.
- S8: a CLI permission check describes that CLI's identity, not necessarily the
  existing Git credential. Check the relevant account and repository permission
  without exposing credentials before declaring a publication blocker.
- S8: a clean checkout on the same host tests fresh environments, not a new OS.
  Retain a failed timed test and its unchanged isolated repeat; never extend
  timeouts or omit failures to describe the first run as passing.
