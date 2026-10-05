# S6 evidence

PNG files are actual rendered VVD screenshots returned by the installed SDK's
EmulatorController API. Their matching JSON files retain device timestamps and
host request/receipt times; input JSON retains remote key dispatch times.
These single frames establish UI state, not sync calibration or a video FPS.
No auth token is saved. Large native traces/build logs remain in ignored
`synth_out/s6/`; report copies and trace checksums make measurements auditable.

`catalog.png`: initial Broadcast card with complete focus border/poster.
`catalog-kids.png`: active Kids badge, two softened warnings.
`profile-kids.png`: verified Kids video and whole-excerpt veil.
`kids-household.png`, `settings-kids.png`, `persistence-kids.png`: automatic Kids,
warning Off and retained settings after native termination/relaunch.
`disclaimer.png`, `attribution.png`: D-pad reachable exact copy and credit.
`chip-focus.png`, `skipped.png`, `profile-local.png`: focused skip, target beyond
the cue tail, then sidecar-only Local swap at retained playback position.
`missing-kids.png`, `unprotected-paused.png`, `invalid-track.png`,
`unsupported-media.png`, `catalog-retry.png`, `catalog-recovered.png`: error
states tested using temporarily edited local server metadata. Original catalog
and track bytes were restored in a finally block; no hazardous source was used.

Build, persistence, Kids numerical verification and performance receipts are
separate JSON files. Performance baseline is explicitly historical. See
`../../S6_REPORT.md` for final measured values and limits. Device timestamps
use the VVD clock (Oct 5); host runs were Oct 6 IST. Do not retime captures.

`final-trace-summary.sql` queries the SDK's Perfetto traces; input latency is
parsed from `debug.value.latencyMs`, not `slice.dur`. `trace-summary.sql` is the
older PID-specific baseline query. Native frame counters may include other
surfaces; retain surface/process context and do not attribute every drop to rAF.

`chrome-hidden.png` / `chrome-shown.png`: verified playback after seven seconds
and controls restored by Up. `launch-report.json` is the final app-first-frame
run; `launch-baseline-report.json` is the historical run associated with
`performance-baseline.json`. These are separate from first video frame.
