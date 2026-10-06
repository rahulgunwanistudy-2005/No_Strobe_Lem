# No Strobe-lem — 3-minute demo video

Record on the deployed build: Vega Virtual Device window at 1080p, plus terminal and report.html. Voiceover recorded separately, ~150 wpm, captions on, public YouTube, English. Every number on screen is copied from `eval/RESULTS.md` headline (placeholders `{{…}}` below).

**Photosensitivity rule for this video:** no unmitigated hazardous sequence at full speed, ever. "Before" is shown as a frame strip, a luminance trace, or ≤ 2 fps stills. Open with a 2-second text card: "This video contains no flashing sequences."

| Time | Screen | Voiceover | On-screen text |
|---|---|---|---|
| 0:00–0:08 | Text card, then VVD: catalog grid, a kid's cartoon-style CC-BY title focused | "This video contains no flashing. That's the point." | "Contains no flashing sequences" |
| 0:08–0:28 | Frame strip of a strobe scene (stills), luminance trace spiking | "For 3 to 5 percent of people with epilepsy, flashing light can trigger a seizure. Broadcasters have rules for this. Streaming apps mostly don't." | "~50M people with epilepsy · 3–5% photosensitive" (source chip) |
| 0:28–0:40 | Title card | "No Strobe-lem gives video a hazard track — like captions, but for your eyes." | Logo + tagline |
| 0:40–1:05 | Terminal: `nostrobe analyze` on the clip; then report.html event table | "We analyze each video once against ITU-R BT.1702, the broadcast standard: brightness swings, saturated red, how much of the screen, how many times a second." | "{{n}} hazard segments · BT.1702-3" |
| 1:05–1:30 | report.html: before/after luminance trace for one segment; verifier box green | "For each segment we compute the weakest veil that brings it under the limits — then re-run the full checker on the veiled result, shifted by the worst sync error we measured on the device." | "FAIL → PASS at ±{{tol_ms}} ms" |
| 1:30–2:00 | VVD: playback; scrubber shows red ticks; hazard-ahead chip appears; veil engages (scene softly dims), chip dismissed | "On Fire TV, nothing changes until it needs to. Three seconds before a hazard you get a heads-up, and the screen softens just enough, only for those seconds." | "Veiled {{veiled_pct}}% of runtime · mean strength {{mean_alpha}}" |
| 2:00–2:15 | Settings: switch to Kids profile; badge count updates; press OK to skip a segment | "Kids gets a stricter profile, automatically. Or skip the segment with one press." | "Kids profile · stricter limits" |
| 2:15–2:35 | Split: S3 upload → catalog updates (sped up) / RESULTS.md headline | "Publishers drop a file into S3; minutes later every profile has a verified track. On {{n_clips}} test clips, zero missed hazards, and every veiled segment re-verifies." | "0 missed hazards / {{n_clips}} · 100% re-verified · {{xrt}}× real-time" |
| 2:35–2:50 | `hazardtrack` repo + web example (overlay/trace only) | "HazardTrack is open source, so any Vega or web player can ship it." | "Apache-2.0 · works in any HTML5 player" |
| 2:50–3:00 | Logo | "No Strobe-lem. Captions for your eyes." | Disclaimer line (bible §5) |

## Recording checklist
- Run `nostrobe eval` and freeze RESULTS.md before recording; fill placeholders from it.
- Release build (no raw mode).
- Show the Vega Virtual Device window title/frame so judges see it's Fire TV/Vega.
- Attribution card for CC-BY footage at the end (≤ 2 s) and in the description.
- No third-party trademarks or music without rights.
