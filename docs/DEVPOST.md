# No Strobe-lem — Devpost draft

**Tagline:** Captions for your eyes: portable HazardTrack sidecars bring verified flash reduction to a Vega player.

**Track:** Fire TV. **Mini challenges:** Open Source; AWS Builder implementation, with live cloud acceptance still pending. This is prepared copy, not a submitted form.

## Inspiration

Carreira et al.'s 2015 paper describes flashing-video analysis and cites roughly 50 million people with epilepsy, with 3–5% affected by flashing light or patterns. These are historical figures from [the paper](https://doi.org/10.1109/QoMEX.2015.7148104), not a new prevalence measurement. Broadcast flashing guidelines prompted us to ask how a player could carry timed viewing-aid information alongside video, like captions.

## What it does

No Strobe-lem analyzes explicitly tagged SDR video, detects luminance/red flashes and prolonged flashing, searches a gray-veil grid for minimum measured distortion, and checks the complete veiled output including ramps at measured VVD sync offsets. It distributes source-bound JSON/WebVTT sidecars and a numerical HTML report. Broadcast, Local and Kids are distinct viewing policies; product choices are documented separately from source rules.

The Vega app waits for a matching verified sidecar, initializes native playback and overlays the scheduled veil. D-pad users can select profiles, see the hazard map and skip with one press. Kids household selects Kids automatically. Invalid or unresolved sidecars refuse protected playback. The bundled demo's Broadcast/Local veil is illustrative; Kids suppresses measured warning events. It is not raw hazardous footage.

## How we built it

Python, NumPy, Numba, ffmpeg and frozen Pydantic contracts form a deterministic engine. Original display-code Y/RGB samples preserve compositing fidelity before averaging on a linear-light grid. The solver and verifier share playback semantics with TypeScript conformance fixtures.

React Native for Vega calls `@amazon-devices/react-native-w3cmedia` through `tv/src/player/VegaW3CPlayer.ts` and `VideoSurface.tsx`; the media clock, scheduler and `VeilLayer.tsx` implement the overlay. [README runtime hooks](../README.md#runtime-hook) identify exact runtime files and the VVD quickstart.

`infra/template.yaml` connects S3 ingest to a bounded Lambda container. Local/read-only-container checks execute the real three-profile engine; publication is refused before any media upload unless every profile verifies. The live AWS deployment, public policy, latency, costs and teardown remain unmeasured. No cloud performance figure or Kiro usage is claimed.

## Results

<!-- submission-results:start -->
Copied from [RESULTS.md](../engine/eval/RESULTS.md) and its machine-readable results; these are synthetic/composite corpus scores.

| Profile | Missed / must-fail | False alarms / must-pass | Veiled runtime | Mean α |
|---|---:|---:|---:|---:|
| broadcast | 0 / 96 | 0 / 229 | 27.8428% | 0.432571 |
| local | 0 / 108 | 0 / 217 | 31.2563% | 0.430608 |
| kids | 0 / 142 | 0 / 183 | 44.8651% | 0.458386 |

975/975 profile tracks re-verify at −268.875, 0, +268.875 ms; 0 unresolved segments.
<!-- submission-results:end -->

Scores concern seeded synthetic boundaries/shapes and injected hazards over licensed footage. The original film control has unadjudicated flags; it cannot establish zero natural-film false alarms. PEAT was not run. S6 observed video drops on VVD and the zero-drop objective remains open. These limits are part of the submission, not omitted from the results.

## Prior art and contribution

[Harding FPA](https://www.hardingfpa.com/) analyzes broadcast flash/pattern hazards. [PEAT](https://trace.umd.edu/photosensitive-epilepsy-analysis-tool-peat-user-guide/) analyzes captured web/software content. [Flikcer](https://arxiv.org/abs/2108.09491) identifies trigger timestamps and offers modified video; [Carreira et al.](https://doi.org/10.1109/QoMEX.2015.7148104) describe efficient BT.1702 detection. Detection and modification precede this project.

Our contribution is a versioned, portable sidecar that carries measured mitigation to players, a closed-loop simulation check under measured VVD timing error, and a Vega reference app with per-viewer profiles. We do not claim an independent comparison with those tools or guarantees beyond the measured setup.

## Challenges and feedback

Actual rendered captures exposed a limited-Y/RGB mismatch; a perfect-looking RGB fit alone was insufficient. Integer PTS resolved a Linux/macOS flash-window disagreement without changing truth or thresholds. Native restart tests caught a storage API that silently lost Kids settings. Release package inspection caught leftover Debug stimuli. S8 serialized rapid seeks and rejected malformed metadata with typed errors.

[Product feedback](PRODUCT_FEEDBACK.md) contains one evaluation per used tool, including onboarding, strengths, weaknesses and whether we would build again. [Friction log](FRICTION_LOG.md) preserves distinct reproductions and honest severity. [Feature requests](FEATURE_REQUESTS.md) arise from those observations.

## Safety

No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.

## Next steps

Resolve SDK dependency advisories, record the deployed AWS path, investigate VVD video drops on physical hardware and adjudicate original-film flags. HDR, regular-pattern hazards and live look-ahead are later scope.

## Open-source mini challenge

Repository: [hazardtrack](https://github.com/rahul-software-dev/hazardtrack). GitHub username: **rahul-software-dev**. [Contribution details and dated creation evidence](OSS_SUBMISSION.md).

I extracted the portable format, deterministic Python engine, schema, browser reader and conformance tests into an Apache-2.0 library with independent CI. The product pins its published release. This gives publishers and player developers a reusable carrier for verified mitigation without adopting the TV app or AWS pipeline.

## Built with and attribution

Python, NumPy, Numba, ffmpeg, TypeScript, React Native, Vega OS, W3C Media, WebVTT, AWS SAM, Lambda containers and S3 contracts. [Apache-2.0](../LICENSE). Blender Foundation / Peach and Mango footage is credited with licenses and modifications in [ATTRIBUTION.md](ATTRIBUTION.md). No public demo URL is claimed until the final recording exists.
