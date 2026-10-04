# No Strobe-lem

Offline SDR video analysis with portable HazardTrack sidecars and a planned Vega OS viewing aid.

**Session 2 engine:** validated contracts, luminance/color helpers, streaming decoding, seeded synthetic media, and detection of SDR luminance/red flashes and prolonged flashing across Broadcast, Local and Kids profiles. Mitigation, verified track publishing, the TV app and AWS processing are gated later work. Detection-only results do not establish safety or certification.

No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.

## Development

Requirements: Python 3.12, uv, Node.js 24 and ffmpeg/ffprobe ≥6 with libx264. Exact Python and JavaScript dependencies are pinned in lockfiles.

```sh
npm ci
cd engine
uv sync --locked
uv run nostrobe schema
uv run ruff check
uv run ruff format --check
uv run mypy --strict src
uv run pytest -q
cd ..
npm run types:check
npm run typecheck
```

Schema changes require `npm run types:generate` after regenerating the Python schema. Both committed outputs are checked in tests/CI. [HazardTrack contract](spec/HAZARDTRACK.md).

```sh
cd engine
uv run nostrobe synth --suite smoke
```

**Warning:** generated clips contain hazardous flashing. They go to ignored `synth_out/` with `HAZARD_` prefixes and truth sidecars. Do not autoplay or watch them. Use numerical traces. The committed smoke manifest is `engine/eval/smoke_manifest.json`; no raw clips are committed.

Analyze without playback, sharing one decoding pass across all profiles:

```sh
uv run nostrobe analyze video.mp4 --detect-only --output events.json
uv run nostrobe analyze video.mp4 --detect-only --profile broadcast
```

Detection JSON carries `verified: false` and cannot be written with a `.hzt.json`/`.hzt.vtt` extension. Without `--output`, JSON goes to stdout. Profile choices are `all` (default), `broadcast`, `local`, and `kids`; each includes its parameter hash. `schema`, `synth`, and detection-only analysis work. Full `analyze`, `verify`, `report`, and `eval` explicitly refuse work until their implementation sessions. Expected error exit codes: 1 validation/filesystem, 2 decode, 3 unsupported media, 4 verification failure, 5 invalid profile, 6 unimplemented stage. Logs are JSON on stderr.

Configuration is read only in `nostrobe.config.Settings`: `NOSTROBE_REPO_ROOT`, `NOSTROBE_FFMPEG`, `NOSTROBE_FFPROBE`, `NOSTROBE_LOG_LEVEL`. Pass `--output` to select the schema or synth output directory. For a packaged installation outside this checkout, set `NOSTROBE_REPO_ROOT` explicitly.

Luma-only media support: explicitly tagged limited-range 8-bit planar YUV SDR. Detection with RGB requires BT.709 transfer, primaries and matrix tags. Decode defaults to 640×360, then averages in cd/m² to 160×90 cells. Tests cover flat-gray recovery, full-resolution synthetic comparisons and variable presentation timestamps. Caller must close a partially consumed frame iterator (`contextlib.closing`) to reap its subprocess immediately. Wider media coverage and production evaluation are later gates.

Lane A: macOS arm64, Vega SDK 0.24.12112 / CLI 1.4.2; stock hello-world built and reached VISIBLE on the Vega Virtual Device. The app directory remains a README until S5. See [Session 1 report](docs/S1_REPORT.md), [Session 2 report](docs/S2_REPORT.md), [interpretations](docs/INTERPRETATIONS.md), [tool feedback](docs/PRODUCT_FEEDBACK.md), and [build safety](docs/SAFETY.md).

Licensed under Apache-2.0. No AWS resources are deployed.
