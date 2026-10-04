# No Strobe-lem — Project Bible (save as `CLAUDE.md` in repo root)

Read this whole file at the start of every session, then `tasks/lessons.md`. Follow the engineering-workflow gates (plan → scaffold → vertical slices → self-review → quality gates → document). When this file and a session prompt disagree, this file wins; flag the conflict in your report.

---

## 1. Product in one paragraph
**No Strobe-lem** analyzes a video once, offline, against the published broadcast rules for photosensitive-epilepsy (PSE) hazards (ITU-R BT.1702-3, Ofcom), and emits a **HazardTrack**: a timed sidecar, shipped next to the video like a caption file. The Fire TV app (Vega OS) reads the HazardTrack and lays a **veil** (a uniform translucent gray layer) over the video just before each hazardous segment, at the minimum strength that makes the segment pass the same rules. A closed-loop verifier re-runs the checker on the simulated veiled output, under the worst-case sync error measured on the device, before any track is published. Viewers pick a profile (Broadcast, Local, Kids); a "hazard ahead" chip offers to skip.

Tagline: *"Captions made TV accessible to deaf viewers. Hazard tracks make it safe for photosensitive ones."*

Names: product **No Strobe-lem**, Python package and CLI **`nostrobe`**, open format **HazardTrack** (`.hzt.vtt` / `.hzt.json`).

## 2. Why this wins (map every decision to the rubric)
Judging: four equally weighted criteria scored 1–5 (Tech Implementation, Design, Potential Impact, Quality of the Idea), friction-log bonus up to 10%, ties broken on Tech Implementation first.

| Criterion | What earns a 5 here | Where it lives |
|---|---|---|
| Tech Implementation | Standards-exact detector, provably sufficient mitigation, verifier under measured sync error, real Vega W3C media integration | §10–§13, §16 |
| Design | Invisible when safe; one D-pad flow; hazard map on the scrubber; Kids profile automatic | §16 |
| Potential Impact | A portable format any Vega/HTML5 app can adopt; publisher compliance path; family viewing | §15, §18 |
| Quality of the Idea | Computer vision on Fire TV with no camera; "captions for your eyes" framing; honest prior-art positioning | §4, §19 |
| Friction bonus | Real, reproducible entries logged as they happen | §21 |

## 3. Scope
**In (v1):** SDR VOD content (H.264/H.265 MP4 or HLS the player can open); luminance flash, saturated-red flash, extended flashing; three profiles; veil mitigation; HazardTrack WebVTT + JSON; CLI + HTML report; Vega app; AWS ingest pipeline; open-source spec + reference library.

**Stretch (only after S8 gates pass):** spatial/regular-pattern hazards; HDR (BT.1702-3 PQ/HLG curves); Fire OS lane polish.

**Out:** live TV, other apps' content (Netflix etc.), on-device pixel analysis, any medical claim, accounts/login, a database.

## 4. Standards facts — the only rules the engine encodes
Source documents (agent: download and read these before S2; quote nothing longer than needed; cite section numbers in code docstrings):
- **ITU-R BT.1702-3 (11/2023)** — free PDF at itu.int (`R-REC-BT.1702-3-202311-I!!PDF-E.pdf`). Primary rule set.
- **Ofcom Guidance Note on flashing images and regular patterns** — free PDF at ofcom.org.uk.
- **WCAG 2.2** definition of "general flash and red flash thresholds" — used only for the saturated-red definition, which BT.1702 does not formalize.

Encoded rules (verify each against the source text before coding; if the text differs, the text wins and you log a lesson):
1. A flash is a pair of opposing luminance changes (increase then decrease, or the reverse).
2. When the darker image is below 160 cd/m², a change counts if the difference is ≥ 20 cd/m². When the darker image is ≥ 160 cd/m², the criterion is relative contrast; BT.1702 states the curve is continuous at 160 (20/(160+20+160) = 1/17 Michelson). Implement as threshold `thr(L_dark) = max(20, L_dark / 8)` cd/m² and unit-test continuity at 160.
3. Irrespective of luminance, a transition to or from a saturated red is potentially harmful.
4. A sequence is hazardous when **both**: combined concurrent flash area > 25% of the displayed screen, **and** more than three flashes (six changes) within any one-second period.
5. Successive flashes whose leading edges are separated by 9 frames or more are acceptable. The rule is written for 25 fps; encode it as a time constant `9/25 s = 0.36 s` and document the frame-rate generalization.
6. Screen luminance comes from the SDR signal-level → cd/m² relation published in BT.1702-3 (anchor: 10-bit code 400 → 20.1 cd/m² for SDR). Transcribe the table into `luminance/bt1702_sdr_curve.csv` with a header citing the source page; never hand-tune it.
7. Extended flashing (Ofcom): flag sequences that keep flashing beyond 5 s even if each second is within limits — `warn` severity only.

Interpretations we choose (product decisions, documented in `docs/INTERPRETATIONS.md`, never presented as the standard):
- Count is "> 6 qualifying changes in any 1 s window" (conservative reading of "more than three flashes").
- Area is evaluated per frame-transition as the fraction of grid cells whose own 1-s change count is hazardous.
- Saturated red: WCAG 2.2 definition (red ratio R/(R+G+B) ≥ 0.8 on the state, plus a chromaticity difference > 0.2 in CIE 1976 u′v′ between states). Agent verifies exact wording and whether R,G,B are linearized before coding.

## 5. Copy and safety language (UI, README, video, Devpost)
Allowed: "reduces flash intensity to within ITU-R BT.1702 limits", "flags sequences that exceed broadcast flashing guidelines", "a viewing aid", "not a medical device".
Forbidden: "seizure-proof", "prevents seizures", "medically safe", "certified", "Harding-compliant", any statistic not in §19 sources, any claim about content we did not analyze.
Fixed disclaimer (UI settings page + README + Devpost): *"No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy."*

## 6. Architecture
```
            ┌──────────────── offline (Python, AWS Lambda) ─────────────────┐
 video ──►  decode (ffmpeg, Y + RGB @ analysis grid)                          │
            → luminance model (BT.1702 SDR curve, linear-light averaging)     │
            → detectors (luma flash, red flash, extended) → events            │
            → veil solver (min-strength veil per merged segment)              │
            → verifier (re-check simulated veiled output at sync offsets)     │
            → HazardTrack .hzt.vtt + .hzt.json + report.html → S3 public/     │
            └───────────────────────────────────────────────────────────────┘
                                   │ catalog.json + tracks + video URLs
                                   ▼
   Vega app: W3C VideoPlayer + KeplerVideoSurfaceView
             + VeilLayer (RN View, gray, animated opacity) above the surface
             + VeilScheduler (drift-corrected media clock, lead/tail, ramps)
             + UI: profile picker, hazard-ahead chip/skip, scrubber hazard map
```
LLMs: **none in the product path.** Every decision is deterministic and reproducible. (Coding agents, Kiro, and the Amazon Devices Builder Tools MCP are dev tools only.)

## 7. Stack (pin exact versions in lockfiles)
- Engine: Python 3.12, `uv`, numpy, pydantic v2, typer, jinja2, matplotlib (report charts, Agg backend), hypothesis, pytest, ruff, mypy `--strict`. ffmpeg/ffprobe ≥ 6 via subprocess (no OpenCV, no PyAV).
- Contracts: pydantic models → JSON Schema (`spec/schema/hazardtrack.schema.json`) → TS types via `json-schema-to-typescript` (`tv/src/types/hazardtrack.ts`, generated, never hand-edited).
- TV app: React Native for Vega (TypeScript strict), `@amazon-devices/react-native-w3cmedia` (`VideoPlayer`, `KeplerVideoSurfaceView`), jest for pure-TS modules, eslint. Reference only (check license before copying code): `AmazonAppDev/vega-video-sample`.
- Dev tooling: Vega CLI (`vega virtual-device start`, `vega run-app …`), Amazon Devices Builder Tools MCP configured in the coding agent (record what it helped with for product feedback).
- Infra: AWS SAM; S3; Lambda (container image with static ffmpeg + `nostrobe`); S3 static hosting of `public/` prefix only.

**Host constraint:** the Vega SDK supports macOS 10.15+ and Ubuntu 20.04+ only (native, ~20 GB disk). If the dev machine is Windows, use Lane B (§16.6) or dual-boot Ubuntu. Decide in S1.

## 8. Repo layout (monorepo; the OSS split in S7 extracts `engine/` + `spec/`)
```
nostrobe/
  CLAUDE.md  README.md  LICENSE (Apache-2.0)
  engine/
    pyproject.toml
    src/nostrobe/
      config.py                 # only place env/paths are read
      cli.py                    # typer: analyze, verify, report, synth, eval
      domain/models.py          # §9 contracts
      domain/profiles.py        # §12
      decode/ffmpeg.py          # probe + frame iterators
      luminance/curve.py  luminance/bt1702_sdr_curve.csv  luminance/color.py
      detect/zigzag.py          # vectorized change detector
      detect/luma_flash.py  detect/red_flash.py  detect/extended.py
      detect/area.py            # global + local-window area rules (summed-area table)
      detect/events.py          # frame mask → merged HazardEvents
      veil/composite.py         # exact veil compositing model
      veil/solver.py            # min-strength veil per segment
      verify/verifier.py        # closed loop incl. sync offsets
      track/webvtt.py  track/jsonio.py
      report/html.py  report/templates/report.html.j2
      synth/generator.py        # §19 synthetic hazard suite
      synth/composite_real.py   # hazards composited onto CC-BY footage
    tests/  (mirrors src)
    eval/run_eval.py  eval/RESULTS.md  eval/manifest.yaml
  spec/
    HAZARDTRACK.md  schema/hazardtrack.schema.json  examples/
  tv/
    src/
      App.tsx
      player/PlayerAdapter.ts  player/VegaW3CPlayer.ts
      veil/VeilLayer.tsx  veil/scheduler.ts  veil/mediaClock.ts
      track/load.ts  track/parseWebvtt.ts
      ui/ProfilePicker.tsx  ui/HazardAheadChip.tsx  ui/HazardScrubber.tsx  ui/Catalog.tsx  ui/Settings.tsx
      catalog/api.ts  config.ts
      types/hazardtrack.ts      # generated
    __tests__/
  infra/
    template.yaml  lambda/Dockerfile  lambda/handler.py
  docs/
    INTERPRETATIONS.md  FRICTION_LOG.md  PRODUCT_FEEDBACK.md  AWS.md  ATTRIBUTION.md  SAFETY.md
  tasks/todo.md  tasks/lessons.md
```

## 9. Data contracts (implement verbatim in `domain/models.py`; frozen pydantic models; times are seconds as float, media timeline)
```python
HazardKind = Literal["luma_flash", "red_flash", "extended_flashing"]   # "pattern" reserved (stretch)
Severity   = Literal["fail", "warn"]
ProfileId  = Literal["broadcast", "local", "kids"]

class HazardEvent(BaseModel):
    id: str                       # "evt_0003"
    kind: HazardKind
    severity: Severity
    t_start: float; t_end: float  # t_end > t_start
    peak_changes_per_s: int       # max qualifying changes in any 1-s window
    peak_area_fraction: float     # 0..1 (global or local-window per profile)
    peak_delta_cd_m2: float | None
    regime: Literal["absolute", "relative", "red"]

class VeilCue(BaseModel):
    id: str
    t_on: float                   # veil reaches full strength at t_on (= first covered t_start - lead)
    t_off: float                  # veil begins ramp-out at t_off (= last covered t_end + tail)
    ramp_in_s: float; ramp_out_s: float   # ≥ params.min_ramp_s
    alpha: float                  # 0..1 overlay opacity
    gray: float                   # 0..1 overlay gray level (display code value)
    covers: list[str]             # HazardEvent ids

class VerifierResult(BaseModel):
    passes: bool
    offsets_checked_s: list[float]
    residual_events: list[HazardEvent]   # must be [] to publish
    engine_version: str; params_hash: str

class MediaInfo(BaseModel):
    content_id: str; duration_s: float; fps: float; width: int; height: int
    transfer: Literal["sdr"]; source_sha256: str

class HazardTrack(BaseModel):
    format: Literal["hazardtrack"]; format_version: Literal["1.0"]
    profile: ProfileId
    media: MediaInfo
    events: list[HazardEvent]
    veils: list[VeilCue]
    verifier: VerifierResult
    generated_at: datetime           # tz-aware UTC
    stats: TrackStats                # veiled_fraction_of_runtime, mean_alpha, n_events_by_kind
```
One HazardTrack per (content, profile). Schema generation is a CLI command; a test fails if the committed schema or generated TS types drift.

## 10. Luminance model
- Decode the **luma plane** (`gray`, limited range) at the analysis grid via ffmpeg; convert 8-bit Y′ to 10-bit code (`×4`), map through the BT.1702 SDR curve (monotone piecewise-linear interpolation of the transcribed table) to cd/m².
- Analysis grid: decode at 320×180 then average **in linear light (cd/m²)** to 160×90 cells. Test in S1 that this differs from full-resolution linear averaging by < 1 cd/m² on the synthetic suite; if not, raise decode resolution.
- RGB (for red) decoded at the same grid (`rgb24`, BT.709 matrix, explicit `-vf scale=…:flags=area,format=rgb24`), only for red detection.
- Round-trip test: encode flat gray clips at known codes, decode, assert recovered code ±1 and expected cd/m² from the curve.

## 11. Detection spec
- **Change detector (`detect/zigzag.py`)**: vectorized per-cell zigzag. For each cell track the running extreme since the last registered change; register a change when `|L - extreme| ≥ thr(min(L, extreme))` with `thr(Ld) = max(20, Ld/8)`. Store change timestamps per cell (ring buffer). One frame loop, numpy ops per frame; target ≥ 20× real-time at 160×90 on a laptop core.
- **Luma flash**: per frame-transition, a cell is "hot" if its qualifying changes in the trailing 1-s window exceed 6, after removing changes belonging to flashes whose leading edges are ≥ 0.36 s from the previous flash's leading edge (rule 5).
- **Red flash**: per cell, state = saturated-red per §4; a red change = entering/leaving saturated-red with Δu′v′ > 0.2. Same counting and area rules.
- **Area (`detect/area.py`)**: `broadcast` = hot cells / all cells > 0.25. `local` = max over all windows of size (1/3 W × 1/3 H) of hot fraction > 0.25 (summed-area table; WCAG-inspired 10° field). Report the measured fraction.
- **Events (`detect/events.py`)**: hazardous frames → intervals; merge gaps < `merge_gap_s`; drop nothing. `severity="warn"` for intervals reaching ≥ 80% of any threshold without failing (for UI only; never veiled unless profile says so).
- **Extended (`detect/extended.py`)**: ≥ 3 changes/s in > `extended_area` sustained > 5 s → `warn`.

## 12. Profiles & params (`domain/profiles.py`, frozen dataclass, `PARAMS_VERSION`; hash included in every track)
| Param | broadcast | local | kids |
|---|---|---|---|
| area rule | global > 25% | local window > 25% | local window > 25% |
| changes in 1 s | > 6 | > 6 | > 4 (product choice) |
| veil `warn` events | no | no | yes |
| red rule | on | on | on |

Shared: `min_ramp_s=0.5`, `lead_s=0.25`, `tail_s=0.25`, `merge_gap_s=1.0`, `sync_tolerance_s` (default 0.15; replaced by the S5 measured value, stored in `params.sync_tolerance_s` with a comment citing `eval/sync_calibration.json`), `gray_candidates=(0.0, 0.25, 0.5)`, `alpha_step=0.02`, `max_alpha=0.85`.

## 13. Veil model, solver, verifier
- **Compositing model (`veil/composite.py`)**: overlay blends in display code space: `y_out = (1-α)·y + α·g` on normalized luma code, likewise per RGB channel for red analysis. S5 measures the real Vega compositing; if it differs, update this model and record the fit in `eval/compositing_calibration.json`.
- **Solver**: for each merged segment (events padded by lead/tail, merged within `merge_gap_s`), search `(g, α)` over `gray_candidates × α grid` for the **minimum distortion** (mean |ΔL| cd/m² over the segment) such that the verifier passes for that segment. Red events require `g > 0` (desaturation); the solver discovers this, do not special-case. If no `(g, α ≤ max_alpha)` passes: emit veil at `max_alpha` **and** mark the segment `unresolved` → the app must show the chip and default to skip for that segment. Never silently publish an unresolved segment.
- **Ramps**: veils ramp in/out linearly over ≥ `min_ramp_s`; the ramp itself is part of the simulated output and must not create a hazard.
- **Verifier**: re-run the full detector on the simulated veiled frames for offsets `{-tol, 0, +tol}` (veil timeline shifted relative to video). `passes` only if zero `fail` events at every offset. Publishing (CLI `analyze`, Lambda) refuses to write a track with `passes=false` except as `*.unresolved.hzt.json` for debugging.

## 14. Photosensitivity safety rules for the build itself (non-negotiable)
- The default app build never plays an unmitigated hazardous segment. A "raw" mode exists only behind a dev flag + double confirmation and is excluded from release builds.
- The demo video never shows an unmitigated hazardous sequence at full speed. Show "before" as a frame strip, luminance trace, or ≤ 2 fps slideshow with a warning card.
- Synthetic hazard clips are written to `synth_out/` with `HAZARD_` filename prefixes and a warning in `synth_out/README`. Do not autoplay them anywhere.
- Contributors who are photosensitive must not review raw clips; work from traces.

## 15. HazardTrack format (`spec/HAZARDTRACK.md`)
- **JSON** (`.hzt.json`): the §9 `HazardTrack` object. Canonical.
- **WebVTT** (`.hzt.vtt`): `WEBVTT` header; a `NOTE hazardtrack` block containing the JSON metadata minus events/veils; one cue per `VeilCue` spanning `[t_on - ramp_in_s, t_off + ramp_out_s]` whose payload is the VeilCue JSON on one line. Any HTML5/W3C player can consume it as a `metadata` text track.
- Versioned (`format_version`); unknown fields ignored by readers; readers must refuse tracks whose `verifier.passes` is false.
- Spec includes a 40-line reference reader for HTML5 `<video>` (in `spec/examples/web/`), proving portability beyond Vega.

## 16. TV app spec (Vega OS)
16.1 **Player**: `PlayerAdapter` interface (`load(url)`, `play/pause/seek`, `currentTime`, `playbackRate`, event subscription) implemented by `VegaW3CPlayer` (`VideoPlayer` + `KeplerVideoSurfaceView`; `initialize()` before `src`).
16.2 **Media clock (`veil/mediaClock.ts`)**: `timeupdate` is too coarse; anchor `(mediaTime, monotonicNow)` on every `timeupdate`/`seeked`/`play`/`pause`; predicted time = `anchor.media + (now - anchor.mono) * rate` while playing; clamp, and re-anchor on drift > 100 ms. Pure TS, unit-tested with a fake clock.
16.3 **Scheduler (`veil/scheduler.ts`)**: given cues + predicted time, returns target `{opacity, gray}` per frame (rAF loop); handles seek into the middle of a veil (snap to full strength, no ramp-down below), pause (hold), rate changes, end-of-media. Pure TS, unit-tested.
16.4 **VeilLayer**: absolutely positioned `View` above the surface (higher zIndex), background `rgb(g,g,g)`, opacity animated; measure whether native-driven animation works on Vega and record it.
16.5 **UI**: Catalog (D-pad grid) → Player. Settings: profile Broadcast / Local / Kids (Kids default when a "kids" household profile is chosen), "Warn me before hazards" toggle, disclaimer. Hazard-ahead chip 3 s before a veil or any unresolved segment: "Flashing ahead · OK to skip". Scrubber shows hazard ticks (red = veiled, amber = warn). All focusable, visible focus ring, works with D-pad only.
16.6 **Lane B (only if Vega SDK cannot run on the dev machine)**: same `src/` with a `ReactNativeVideoPlayer` adapter on the Android TV emulator / Fire OS (the hackathon FAQ accepts the Android TV emulator for Fire TV). Scheduler/UI code must not import Vega packages directly — only through `PlayerAdapter`.
16.7 Config from `tv/src/config.ts` only (catalog base URL). No secrets in the app.

## 17. AWS pipeline (`infra/`)
- SAM template: bucket with prefixes `ingest/`, `public/`. S3 `ObjectCreated` on `ingest/*.mp4` → Lambda (container image: static ffmpeg + `nostrobe`; memory 3008 MB; timeout 900 s; ephemeral storage sized to input) → runs `analyze` for all three profiles → writes `public/{content_id}/video.mp4`, `public/{content_id}/{profile}.hzt.vtt|.hzt.json`, `public/{content_id}/report.html`, then rebuilds `public/catalog.json` from listing (idempotent; no read-modify-write races).
- Only `public/*` is readable (bucket policy); `ingest/` private. Least-privilege IAM. Structured JSON logs with `content_id`.
- `docs/AWS.md`: architecture, deploy (`sam build && sam deploy --guided`), teardown, measured cost per analyzed hour of video.
- Credits: use the hackathon $150 AWS credit; tear down when not testing.

## 18. Open source split (Open Source mini challenge)
In S7, create a **separate public repo `hazardtrack`** (Apache-2.0, created during the hackathon window): `spec/`, the Python reference library (`nostrobe` engine minus app/infra), the web reference reader, tests, CI. The product repo depends on it. Record: contribution URL, repo URL, GitHub username, what/how/why (for the submission form).

## 19. Evaluation (S4) and the gate
Synthetic suite (seeded, `synth/generator.py`), each clip with analytic ground truth:
- Boundary pairs per rule: 3.0 vs 3.5 flashes/s; area 24% vs 26%; ΔL 19 vs 21 cd/m² at dark=100; dark=150 vs 170 regime switch; leading-edge spacing 0.34 vs 0.38 s; red pairs at/below/above the chroma threshold; isolated single/double/triple flashes (must pass).
- Shapes: full-frame, quadrant, scattered tiles summing to area, moving bar, camera-flash bursts, police-light red/blue alternation, lightning, glitch cuts; fps ∈ {24, 25, 30, 50, 60}.
- Realistic set: hazards alpha-composited onto CC-BY footage (Blender open movies; attribution in `docs/ATTRIBUTION.md`).
- Clean control: unmodified CC-BY films → expect zero `fail` events; any found are reviewed and reported honestly.
Metrics (`eval/RESULTS.md`, regenerated by `python -m nostrobe.cli eval`, deterministic): clip-level detection confusion matrix; interval IoU vs ground truth; **missed hazards (FN) on the must-fail set**; false alarms on must-pass and clean sets; verifier pass rate after veiling at all offsets; viewing cost (veiled fraction of runtime, mean α, mean |ΔL|); analysis speed (× real-time).
**Hard gate: FN = 0 on the must-fail set and verifier pass = 100% (or segments correctly marked unresolved).** If a gate fails, fix logic, never the test or the ground truth.
Optional: PEAT (free, Windows) cross-check on a subset; if not run, `RESULTS.md` says so.
Impact statistic allowed in copy: "Epilepsy affects around 50 million people worldwide; 3–5% of them have seizures triggered by flashing light or patterns" — source: Carreira et al., "Automatic detection of flashing video content" (2015), cite in Devpost.

## 20. Engineering standards
- Thin entry points; modules by concern; typed boundaries; config at the edge; tests mirror source.
- Python: `ruff check`, `ruff format --check`, `mypy --strict src`, `pytest -q` all clean. TS: `tsc --noEmit`, eslint, jest clean. Vega app builds and runs on the Vega Virtual Device.
- Seeds everywhere; no wall-clock in engine outputs except `generated_at`; float comparisons with tolerances.
- No bare `except`; typed errors (`DecodeError`, `UnsupportedMediaError`, `VerifierFailedError`); CLI maps them to exit codes and one-line messages.
- No debug prints; structured logging only. Minimal comments.

## 21. Friction log & product feedback (judging bonus up to 10%)
Log in `docs/FRICTION_LOG.md` **when it happens**, format in `12_FRICTION_LOG_TEMPLATE.md`. Only real, reproduced issues; include commands and versions. Also maintain `docs/PRODUCT_FEEDBACK.md` per tool used (Vega SDK/CLI, Vega Virtual Device, W3C Media, Amazon Devices Builder Tools MCP, Vega Studio, AWS SAM/Lambda/S3, Kiro if used): what it was used for, what worked, what needs work, onboarding, would-build-again.

## 22. Agent rules
1. Plan in `tasks/todo.md` before code; report at session end: built, verified (command outputs summarized), deferred.
2. Never rewrite git history, never force-push, never commit secrets. Rahul commits.
3. Never invent numbers, thresholds, or citations. If a source can't be fetched, stop and say so.
4. Never weaken a test or gate to make it pass.
5. Ask only when a decision changes the architecture; otherwise decide, document in `docs/INTERPRETATIONS.md` or `tasks/todo.md`, and continue.
