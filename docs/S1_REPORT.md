# Session 1 report

Completed 2026-10-04. Scope: the three supplied documents and their Session 1 build instructions. Later build sessions were not started.

## Built

- Monorepo scaffold with Apache-2.0 license, Python 3.12 engine, exact uv/npm lockfiles, configuration at the edge, JSON logging, typed errors and six CLI commands. `schema`/`synth` work; later commands and modules refuse with explicit unimplemented errors. TV remains a README. Infra remains undeployed scaffolding.
- Frozen, validated Pydantic contracts; three frozen profile dataclasses and versioned stable SHA-256 hashes; canonical JSON Schema; generated TypeScript with drift checks; strict TypeScript compilation. The example track is an unverified, fabricated contract fixture and must be refused by readers.
- SDR Table 1 transcribed from BT.1702-3 (11/2023), visually inspected, cross-checked against -2 (10/2019), with edition/page/source header and source hashes. Piecewise-linear conversion, inverse synthesis map, continuous boundary helper, sRGB/BT.709 helpers, CIE u′v′ and red-transition helpers.
- Bounded streaming ffmpeg decoding with presentation timestamps, subprocess cleanup and stderr tails. Raises typed errors on unsupported transfer/unknown range/unsupported pixel formats. Linear-light cell averaging. Variable-frame-rate timing is tested.
- Seeded synthetic primitives: flat gray, full/regional/tile flashes, RGB alternation, moving bar, camera burst, lightning, police lights, isolated one/two/three pulses, hard-edge checker. Analytic truth sidecars use sampled frame-index counting independently of the future detector. Raw videos are ignored and never autoplayed; only the manifest is committed.
- Vega Lane A installed and exercised: CLI 1.4.2, SDK/VVD 0.24.12112. Stock hello-world built and ran on aarch64 VVD. `vlcm list` showed `VISIBLE`, pid 4860, and the device was stopped; final status was `running:false`.
- Amazon Devices Builder Tools MCP 1.0.15 configured locally; CLI tools, workflow inventory and installation workflow verified. Feedback and one reproduced CLI-friction entry recorded.

## Verified

Exact final engine gate (from `engine/`):

```sh
uv run ruff check && uv run ruff format --check && uv run mypy --strict src && uv run pytest -q
```

Result: all checks passed; 45 Python files formatted; strict types clean for 35 source files; **68 tests passed in 19.53 s**. Tests cover contract validation/round-trips, schema/TypeScript drift, stable profile hashes, sourced anchors, monotonicity, vector/scalar equivalence, threshold continuity, color boundaries, error paths, grayscale round-trips, VFR timestamps, early iterator cleanup and spatial fidelity across every luma smoke clip.

`npm run types:check && npm run typecheck`: both passed. `git diff --check`: passed. A distributable wheel built and includes the sourced CSV.

`uv run nostrobe synth --suite smoke`: **16 clips and truth sidecars in 6.42 s**, below 60 s. All 16 independently probed: 640×360, 25 fps, H.264/yuv420p, limited range, BT.709 transfer/primaries/matrix. Flat codes {16,64,128,200,235} recovered within the unchanged ±1-code requirement. SDR anchors D=400 and D=863 pass the requested tolerances.

The initial 320×180 spatial gate failed. Raising decode to 640×360 and improving synthetic encoding fidelity passed the unchanged <1 cd/m² gate. Measured maximum over every frame/cell of all luma smoke clips: **0.4555 cd/m²**. Raw measurements are in `s1_measurements.json`; this is build validation, not the S4 product evaluation.

## Conflicts, interpretations and limits

- User explicitly authorizes commits; that overrides the bible's “Rahul commits” default. Commit messages have no attribution trailers. No history is rewritten.
- The bible wins over session prompts; published source wording wins over shorthand rules per its source-verification instruction. BT.1702's HDR-only relative criterion, 50/60 Hz spacing distinction, strict relative boundary, and WCAG saturated-endpoint wording are documented in INTERPRETATIONS.md. S2 must use these verified distinctions; no standards-exact detector is claimed yet.
- Generated types live temporarily in `spec/generated/` to honor S1's TV-README-only instruction; move them to `tv/src/types/` in S5. The deviation is explicit and drift checks are active.
- SDK run verification uses the device lifecycle manager. Desktop screenshot inspection was unavailable because the Mac was locked. No visual-layout check is claimed. Vega Studio was skipped because VS Code was not found.
- Tagged limited-range 8-bit planar YUV SDR is the S1 decoder scope. RGB assumes BT.709; other primaries/matrices and higher-resolution spatial fidelity require renewed evaluation before content publishing. No HDR, live or medical claims.
- Synthetic truth is analytic raw-sample truth, not post-codec detector results. Psychovisual/adaptive quantization are disabled and max QP 6 supplements CRF 10 to preserve test stimuli. The synthetic suite does not establish product accuracy.
- Local MCP configuration is saved; this chat's callable tools are not hot-reloaded. CLI verification is documented; tool exposure in a fresh client session remains to be checked.

## Deferred by the supplied session scope

Detection (S2); veil/verifier/track publishing/reporting (S3); must-fail/clean/real-footage evaluation and performance claims (S4); Vega player/sync/compositing/UX (S5-S6); AWS and public OSS split (S7); submission/demo hardening (S8). `engine/eval/RESULTS.md` deliberately contains no invented evaluation figures. TS app eslint/Jest/device-media gates begin when the TV app exists.
