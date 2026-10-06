# Devpost write-up — No Strobe-lem

**Tagline:** Captions for your eyes: a verified hazard track that lets Fire TV soften dangerous flashing, only when it's needed.

**Tracks:** Fire TV (primary). **Mini challenges:** AWS Builder, Open Source.

## Inspiration
Epilepsy affects around 50 million people worldwide, and 3–5% of them have seizures triggered by flashing light or patterns (Carreira et al., 2015). Broadcasters screen content against ITU-R BT.1702 and Ofcom rules; streaming apps on TVs have no standard way to carry that information to the player. Deaf viewers got captions. Photosensitive viewers got a warning card, sometimes.

## What it does
- Analyzes a video once against ITU-R BT.1702-3 (luminance flashes, saturated red, area, rate).
- Computes the weakest uniform veil that makes each hazardous segment pass, and proves it by re-running the checker on the veiled result at ±{{tol_ms}} ms, the sync error we measured on the Vega Virtual Device.
- Ships the result as a **HazardTrack** (JSON + WebVTT), next to the video, like captions.
- The Fire TV app (Vega OS) applies the veil in sync, warns 3 s ahead, offers one-press skip, shows hazards on the scrubber, and has Broadcast / Local / Kids profiles.

## How we built it
- Engine: Python, numpy, ffmpeg. Vectorized per-cell change detection on a 160×90 linear-light grid; BT.1702-3 SDR luminance curve; summed-area-table area rules; minimum-distortion veil search; closed-loop verifier.
- TV: React Native for Vega, `@amazon-devices/react-native-w3cmedia` (`VideoPlayer`, `KeplerVideoSurfaceView`), a drift-corrected media clock and a scheduler that matches the engine's playback semantics exactly (shared conformance fixture).
- AWS: S3 → Lambda (container with ffmpeg + engine) → verified tracks, reports, catalog. {{Kiro usage, only if true}}.
- **Runtime hook:** see README "Runtime hook" (file paths).

## Results (from `eval/RESULTS.md`, reproducible with one command)
| Metric | Value |
|---|---|
| Missed hazards on must-fail set | 0 / {{n_fail}} |
| False alarms on must-pass + clean films | {{fp}} |
| Veiled segments re-verified at ±{{tol_ms}} ms | 100% ({{unresolved}} unresolved, shown as skip-only) |
| Viewing cost | {{veiled_pct}}% of runtime veiled, mean strength {{mean_alpha}} |
| Speed | {{xrt}}× real-time; ${{cost_per_hour}} per analyzed hour on Lambda |

## Prior art and what's new (honest)
Harding FPA (commercial broadcast QC), PEAT (free, web content), Flikcer (browser extension) and research tools (e.g. Carreira et al., real-time BT.1702 analysis) already detect flashing. We did not invent detection. What's new: (1) a portable, versioned **sidecar format** that carries verified mitigation to any player; (2) mitigation that is **proven sufficient** by re-checking the veiled output under measured device sync error; (3) a Fire TV/Vega implementation with per-viewer profiles.

## Safety
No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.

## Challenges
{{from friction log: e.g. timeupdate granularity → media clock; measuring compositing on the VVD}}

## What's next
HDR (BT.1702-3 PQ/HLG), regular-pattern hazards, live content with a look-ahead buffer, system-level HazardTrack support in the Vega player so every app benefits.

## Product feedback (required, one block per tool)
Vega SDK & CLI · Vega Virtual Device · W3C Media for Vega · Amazon Devices Builder Tools MCP · Vega Studio · AWS SAM / Lambda / S3 · {{Kiro}} → copy from `docs/PRODUCT_FEEDBACK.md` (used for / worked well / needs work / onboarding / would build again).

## Feature requests (optional)
From S8 list, with priority.

## Friction log (optional, judging bonus)
Link `docs/FRICTION_LOG.md`; paste entries in the form.

## Open Source mini challenge fields
Contribution URL: {{hazardtrack repo}} · Project repo: {{product repo}} · GitHub username: {{}} · What/how/why: {{3 sentences}}.

## Built with
python, numpy, ffmpeg, react-native, vega-os, typescript, aws-lambda, amazon-s3, aws-sam, webvtt

## Attribution
CC-BY footage: see `docs/ATTRIBUTION.md`.
