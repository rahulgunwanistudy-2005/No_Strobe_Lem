# No Strobe-lem — Build Pack

"Captions made TV accessible to deaf viewers. Hazard tracks make it safe for photosensitive ones."

Fire TV track (Vega OS) · AWS Builder mini · Open Source mini — Amazon "Build, Ship, Shape" (Devpost, deadline Oct 23 2026, 12:00 PT).

## Files
| File | Use |
|---|---|
| `00_PROJECT_BIBLE.md` | Single source of truth. Copy into the repo root as `CLAUDE.md` before S1. Every session prompt assumes the agent has read it. |
| `S1_scaffold_contracts_luminance.md` … `S8_hardening_submission.md` | One pasteable prompt per build session, in order. Each ends with acceptance gates. Do not start S(n+1) until S(n) gates pass. |
| `09_DEMO_SCRIPT.md` | 3-minute video: shot list, voiceover, on-screen numbers, photosensitivity-safe recording rules. |
| `10_DEVPOST.md` | Submission write-up skeleton incl. runtime hook, prior-art disclosure, product feedback, mini-challenge fields. |
| `11_JUDGE_QA.md` | Hard questions and the answers. |
| `12_FRICTION_LOG_TEMPLATE.md` | Exact entry format for the up-to-10% judging bonus. Start logging in S1. |

## Session order and why
1. **S1** Scaffold, contracts, BT.1702 luminance model, synthetic hazard generator. Ground truth first; everything later is tested against it.
2. **S2** Detection engine: luminance flashes, red flashes, extended flashing, area rules, three profiles. Boundary + property tests. Zero-missed-hazard gate.
3. **S3** Veil solver + closed-loop verifier (re-checks the mitigated output under worst-case sync error) + HazardTrack writer (WebVTT + JSON) + CLI + HTML report.
4. **S4** Evaluation harness: synthetic suite metrics, realistic composited hazards on CC-BY footage, false-positive control on clean films. Reproducible `eval/RESULTS.md`.
5. **S5** Vega app core: W3C media player, veil overlay, drift-corrected scheduler, on-device sync + compositing calibration (feeds measured tolerances back into S3).
6. **S6** Vega UX: profiles (incl. Kids), hazard-ahead chip + skip, scrubber hazard map, catalog, D-pad focus. Fire OS fallback lane only if needed.
7. **S7** AWS pipeline (S3 → Lambda container → tracks + reports + catalog) and the open-source `hazardtrack` repo split.
8. **S8** Hardening, docs, runtime-hook README, product feedback, friction log, recordable demo.

## Operating rules
- Paste `00_PROJECT_BIBLE.md` as `CLAUDE.md`. Paste S1…S8 one per session.
- You commit after each session passes its gates. The agent never rewrites git history.
- Every number in the video and the write-up comes from `eval/RESULTS.md`. No invented figures.
- Never put an unmitigated hazardous sequence at full speed in the video or in the default app build (bible §14).

Session sources archived in this checkout: `S1.md` through `S8.md`, plus supporting 09–11 and the friction template.
