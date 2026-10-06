# Judge Q&A

**Does this protect video in other apps?** The current Vega app plays its own catalog. Other apps would need to adopt HazardTrack or platform-level consumption. No analysis of another app's content is claimed.

**Detection already exists.** Yes. The README links Harding FPA, PEAT, Flikcer and Carreira et al. HazardTrack focuses on the portable carrier, timed per-viewer playback veil and full simulated-output check under measured VVD offsets.

**How much does it change the picture?** The search minimizes measured luminance distortion over its candidate grid, then veils only the resulting timeline. The table below describes the evaluation corpus, not a typical household viewing session. Viewers can also skip.

<!-- submission-results:start -->
See [RESULTS.md](../engine/eval/RESULTS.md); current-provenance S8 evaluation is in progress.
<!-- submission-results:end -->

**Can the veil itself introduce flashing?** The verifier checks complete simulated output, including ramps and overlaps, at every stated offset. A passing simulation is limited to the detector/model and analyzed input; it is not an absolute guarantee.

**What if timing slips?** VVD screen recordings established a worst-scenario bound used by the verifier. The app covers seeks, pauses during them and primes destination protection before resuming. Beyond that measured bound, or on another device/player, recalibration is required.

**What happens when mitigation fails?** The engine writes diagnostic unresolved JSON and refuses playable outputs. The player rejects failed/unresolved sidecars entirely. It does not play an unresolved section merely because a skip chip exists. Diagnostic tick/skip mapping still handles unresolved and veiled overlaps.

**What if no track exists?** Playback is paused. An explicit unprotected choice retains a persistent warning banner and never autoplays. Kids focuses keep-paused. Invalid or mismatched analysis offers no such fallback.

**How is correctness assessed?** Independent analytic truth, encoded boundary/shape cases at multiple frame rates, licensed-footage composites, typed-input and contract regressions, and complete post-veil checks. Unmodified-film flags remain unadjudicated and PEAT was not run. Those limits prevent a general natural-content accuracy claim.

**Why deterministic rules?** Published thresholds and explicit product policies are reproducible and inspectable. The report records source hashes, parameter hashes, implementation provenance and retained timing measurements.

**What does AWS do?** The implemented pipeline turns a bounded S3 upload into three verified profiles, report and listing-derived catalog. Real container/SDK-adapter tests pass; live Lambda timing, costs, anonymous policy and teardown are pending credentials/region. No dollar figure is supplied.

**Is this ready for a release claim?** Read [S8 status](S8_REPORT.md). Upstream dependency advisories, live cloud/demo gaps and the recorded VVD performance limitation must remain visible. A release tag is withheld while S8 acceptance is incomplete.

**HDR, regular patterns or live TV?** Current scope is explicitly tagged SDR VOD and the documented flashing detectors. These features are future work; no results are generalized to them.

**Medical claims?** No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.
