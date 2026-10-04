# Standards and product interpretations

Verified 2026-10-04. Standards sources govern over shorthand in the build pack.

- [ITU-R BT.1702-3 (11/2023)](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf): Annex 2, Table 1, printed p.7 (PDF p.9), SDR column transcribed into the CSV. This is a table, not a fitted formula. The values match [-2 (10/2019), Table 1 p.6](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-2-201910-S!!PDF-E.pdf). Annex 2 Figure 3 notes give D=400 → 20.1 and D=863 →160.4 cd/m²; interpolation of rounded table entries is used. Codes below 64 and above 940 clamp to 0 and 200 cd/m². Monotonicity is strict within the reference range, nondecreasing in foot/headroom.
- BT.1702-3 Annex 1 Guideline 1 p.3 specifies the relative criterion above 160 for **HDR only**. S1 implements the continuous `max(20,Ldark/8)` boundary helper requested in the brief. S2 must distinguish this helper from the SDR detector's absolute rule and verify behavior against the source. No standards-exact detector is claimed in S1.
- The relative contrast criterion is strictly greater than 1/17 above the boundary; the low-luminance absolute criterion is ≥20. This distinction must be handled in S2, not hidden in `thr`.
- The source permits leading-edge spacing ≥360 ms in 50 Hz and ≥334 ms in 60 Hz environments. The brief's constant 0.36 s across frame rates is a conservative product interpretation. Profile params preserve that requested constant; frame rate alone does not establish display refresh rate.
- Counting >6 qualifying changes in a trailing `(t-1,t]` window, per-cell area, local 1/3-screen windows, Kids >4 and extended-area 25% are product decisions. Source guidance mentions extended sequences >5 s; the numeric extended-area and change-rate settings are not attributed to the standard.

## Color

[WCAG 2.2 flash-threshold Note 3](https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds) requires a saturated endpoint with R/(R+G+B) ≥0.8 and distance >0.2 in CIE 1976 u′v′. It says **to or from a saturated state**, so a transition between two saturated endpoints is not excluded. The brief's entering/leaving-only formulation is incomplete. Opposing transition pairing is deferred to S2.

WCAG's working-definition note does not explicitly specify the transfer function of the RGB symbols. The project chooses linear RGB for the ratio and XYZ computation. Web sRGB uses WCAG's documented 0.04045 linearization. Video rgb24 uses inverse [BT.709-6 §1.2](https://www.itu.int/rec/R-REC-BT.709-6-201506-I/en); BT.709 primaries/D65 are converted to XYZ using [W3C CSS Color 4 conversion matrices](https://www.w3.org/TR/css-color-4/#color-conversion-code). Black has ratio 0 and undefined chromaticity is represented as (0,0); this conservative black transition convention is a product choice. The display luminance table is separate from these source-color helpers.

## Contracts and scaffold

Pydantic models are frozen with the field names and list containers required by §9. Freezing prevents attribute reassignment, not mutation inside lists/dicts. Readers must revalidate incoming JSON. Unknown fields are ignored. `generated_at` must be aware and is normalized to UTC. Veil times may be negative near the start of media; app clipping belongs to S5. `TrackStats` constrains fractions and counts.

S1 asks for only a TV README, whereas the bible places generated types inside TV. The generated contract is temporarily `spec/generated/hazardtrack.ts`; S5 will move it into `tv/src/types/`. Schema and TypeScript drift checks run in tests/CI. Unimplemented later-stage modules fail explicitly with `NotImplementedError`.

Synthetic truth describes sampled raw primitives under the Broadcast product interpretation, independently of the future detector. It records quantized luma pairs, not requested ideal values alone. Lossy H.264 can alter spatial boundaries/color: S2/S4 must measure this rather than relabel ground truth to fit detection. Smoke clips are not the full S4 evaluation suite.

## Decode resolution and synthesis fidelity

The initial 320×180 grid failed the hard-edge spatial gate, so S1 raises both
luma and RGB decode defaults to 640×360 and averages 4×4 in linear light to
160×90 cells. The gate tests the 640×360 synthetic inputs; higher-resolution
source content needs renewed spatial-error evaluation in S2/S4.

Synth retains CRF 10 and additionally disables x264 psychovisual optimization
and adaptive quantization, with maximum QP 6. The cap is an encoding-quality
choice to preserve analytic test stimuli (not a hazard threshold). Matching
input/output BT.709 and range tags prevents an implicit color conversion.
Explicit x264 VUI tags preserve transfer/primaries metadata across encoders.
