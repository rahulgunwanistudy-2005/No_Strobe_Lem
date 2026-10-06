# Demo readiness — S8

The original [pack shot list](build-pack/09_DEMO_SCRIPT.md) is preserved as source material. Its placeholders and broad claims are not recording-ready copy. The table below walks every shot against actual project evidence and gives a concrete recordable form. **The live cloud shot remains blocked; no finished narrated/public demo is claimed.**

Use the Release package and the attributed no-FAIL opening excerpt, or static traces. Keep the VVD frame/window title visible in the final host recording. SDK screenshots establish rendered app behavior, but do not by themselves capture that host window frame. Never open raw `HAZARD_` video in a player. A complete detection-gate corpus is not a medical guarantee.

| Time | Recordable shot and accurate caption | Evidence / readiness |
|---|---|---|
| 0:00–0:08 | Static warning card: “No unmitigated flashing footage is shown.” Then D-pad catalog focused on the existing Big Buck Bunny card; do not invent a cartoon title. | Current S8 Release catalog snapshot in `evidence/s8/catalog.png`; credited demo artwork/clip. |
| 0:08–0:28 | Static numerical luminance trace, not full-speed “before” footage. If used, show the impact statistic explicitly as a historical estimate cited by Carreira et al. (2015). | `engine/eval/traces/bbb.png`; [paper](https://doi.org/10.1109/QoMEX.2015.7148104). Claim only what those sources say. |
| 0:28–0:40 | Static title card: “No Strobe-lem · Captions for your eyes.” | README pitch and nonflashing timeline schematic are available. |
| 0:40–1:05 | Run `uv run --project engine nostrobe analyze tv/assets/raw/demo.mp4 --out analysis_out/s8-demo/`; open the report event table. State that the source has no FAIL events and the catalog's Broadcast/Local cue is illustrative. | Real analyzed demo report/track artifacts; terminal command is separate from catalog's intentionally added illustration. Do not describe zero FAIL events as a strobe failure. |
| 1:05–1:30 | Static evaluated hazard traces/results plus the verifier offsets and headline table. Explain “complete simulated output rechecked at measured VVD offsets.” | Final `engine/eval/RESULTS.md` and checksum-bound submission metrics. The README GIF is a schematic, not calibrated hazard footage. |
| 1:30–2:00 | Show the actual VVD illustrative overlay, red scrubber ticks and chip, with the label “Illustrative veil on no-FAIL excerpt.” | S5/S6 recordings and current S8 Release checks. Native state alone is insufficient; inspect current rendered frames. |
| 2:00–2:15 | Menu → Settings → Kids, return, focus chip and OK to skip. Do not say an unresolved profile can play. | S6 actual Kids/skip/persistence captures; current S8 native rerun. Invalid/unresolved tracks are refused entirely. |
| 2:15–2:35 | Original shot: upload into live S3 and show real catalog inclusion, then accurate results. **Blocked until AWS credentials/region and real deploy/smoke checks.** A local pipeline demonstration can be recorded only with an explicit “local integration; AWS not deployed” caption. | `infra/smoke.py`, `docs/AWS.md`; S7 adapter/container receipts are local evidence, not cloud latency/cost. No claim of “minutes later” without a measured run. |
| 2:35–2:50 | Public reference repository and portable web reader; show constant-gray overlay capture only. Say “reference HTML5 reader,” not a guarantee for every HTML5 player. | Public [repository](https://github.com/rahul-software-dev/hazardtrack); `docs/s7/web-overlay.mp4` and reader conformance evidence. Other players need calibration. |
| 2:50–3:00 | Static logo/tagline, full fixed disclaimer, attribution card held legibly; no flashing transitions. | README disclaimer and `ATTRIBUTION.md`. Lengthen the attribution hold if needed; omit unlicensed music/trademarks. |

## Capture procedure

Start VVD and the README's local server, install the current Release package, verify source-bound catalog loading, and terminate/relaunch before each take so old native position is not mistaken for a fresh run. Use D-pad only. Preserve original acquisition timestamps and rejected captures. Functional checks performed alongside engine work do not establish new latency/drop measurements.

Before recording, rerun `uv run --directory engine python ../scripts/update-submission.py` against complete current-provenance results. The command refuses stale or incomplete evidence and updates README, Devpost and judge tables together. Read viewing-cost denominators aloud as evaluation-corpus costs, not typical viewing.

The existing caption “This video contains no flashing sequences” should be used only after reviewing the final edited recording itself. A script cannot establish that assertion. Check every cut, screen capture, source frame and end card before publishing. Voiceover/captions, final editing, public upload and a complete live cloud take remain submission tasks.
