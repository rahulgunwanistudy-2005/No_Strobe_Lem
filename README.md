# No Strobe-lem

Offline SDR video analysis with portable HazardTrack sidecars and a planned Vega OS viewing aid.

**Session 3 engine:** detects SDR luminance/red flashes and prolonged flashing, solves display-code veils, verifies the complete simulated output at −0.15/0/+0.15 s offsets, and writes HazardTrack JSON/WebVTT plus a static trace report. Profiles are Broadcast, Local and Kids. Unresolved profiles produce debugging JSON only. Device calibration, the TV app, AWS processing and broader S4 evaluation remain later work. Verification describes the simulation model and does not establish medical safety or certification.

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

Write verified tracks and a report:

```sh
uv run nostrobe analyze video.mp4 --out analysis_out/
uv run nostrobe analyze video.mp4 --profile broadcast --out analysis_out/
uv run nostrobe verify video.mp4 analysis_out/video.broadcast.hzt.json
uv run nostrobe report analysis_out/video.broadcast.hzt.json --video video.mp4 --out report.html
```

Analysis defaults to all profiles. Output names are `<content>.<profile>.hzt.json`
and `.hzt.vtt`; the shared report is `report.html`. Failed profiles write only
`<content>.<profile>.unresolved.hzt.json`, with residual events and explicit
unresolved reasons. Re-analysis removes stale verified outputs for failing
profiles. Readers reject unresolved tracks; the report command permits debug
JSON so failures remain inspectable. Verification checks the video SHA-256
and current parameter hash. JSON logs go to stderr.

Detection-only JSON carries `verified: false`, uses `--output`, and cannot use
a HazardTrack extension. Expected exits: 0 success, 1 validation/filesystem,
2 unresolved verification, 3 unsupported media, 4 decode error, 5 invalid
profile, 6 deferred stage. `eval` remains the broader S4 harness placeholder;
S3 acceptance scripts are in `engine/eval/`.

Decoded Y/RGB bytes are cached in ignored `.nostrobe_cache/`, keyed by source
SHA-256 and decode format. Each frame takes about 0.88 MiB; a ten-minute
24 fps film takes approximately 12.3 GiB. Samples stay memory-mapped and
32-frame shards bound decoding memory. Remove this directory to free disk or
force fresh decoding. Solving may take longer than detection alone, because
it repeatedly checks all detector rules and ramp transitions.

Configuration is read only in `nostrobe.config.Settings`: `NOSTROBE_REPO_ROOT`, `NOSTROBE_FFMPEG`, `NOSTROBE_FFPROBE`, `NOSTROBE_LOG_LEVEL`. Pass `--output` to select the schema or synth output directory. For a packaged installation outside this checkout, set `NOSTROBE_REPO_ROOT` explicitly.

Luma-only media support: explicitly tagged limited-range 8-bit planar YUV SDR. Detection with RGB requires BT.709 transfer, primaries and matrix tags. Decode defaults to 640×360, then averages in cd/m² to 160×90 cells. Tests cover flat-gray recovery, full-resolution synthetic comparisons and variable presentation timestamps. Caller must close a partially consumed frame iterator (`contextlib.closing`) to reap its subprocess immediately. Wider media coverage and production evaluation are later gates.

Lane A: macOS arm64, Vega SDK 0.24.12112 / CLI 1.4.2; stock hello-world built and reached VISIBLE on the Vega Virtual Device. The app directory remains a README until S5. See [Session 1 report](docs/S1_REPORT.md), [Session 2 report](docs/S2_REPORT.md), [Session 3 report](docs/S3_REPORT.md), [interpretations](docs/INTERPRETATIONS.md), [tool feedback](docs/PRODUCT_FEEDBACK.md), and [build safety](docs/SAFETY.md).

Licensed under Apache-2.0. No AWS resources are deployed.
