# Product feedback

Final consolidation, 6 October 2026 IST. Only tools actually used receive an evaluation. Detailed session records remain in [the history](PRODUCT_FEEDBACK_HISTORY.md); [friction entries](FRICTION_LOG.md) provide reproductions.

## Vega SDK / CLI 0.24.12112 / 1.4.2

- Used for: Generate, build, install and inspect native TV packages
- Worked well: Lane A template and all architecture builds; manifest errors visible in native logs
- Needs work: Incremental staging retains deleted raw assets; SDK template audit findings remain after supported updates
- Onboarding zero → hello world: Official installer, source `~/vega/env`, generate helloWorld, build and `vega run-app`; S1 records the real commands
- Would build again: **Yes:** reproducible CLI path and working player; package contents need independent checks

## Vega Virtual Device 0.24.12112

- Used for: Playback, remote focus, storage restart, actual screen capture and calibration
- Worked well: Authenticated SDK screenshots expose rendered pixels and original timestamps
- Needs work: Ready message can precede parent-session shutdown; a running instance needed a VDA server restart before discovery; screenshot discovery is obscure; measured video drops remain
- Onboarding zero → hello world: Start VVD, verify device discovery, install package and use SDK screenshot controller; S5/S6 retain actual evidence
- Would build again: **Yes:** useful repeatable device testing; physical-TV calibration still needed

## W3C Media 2.3.2

- Used for: VideoPlayer, surface attachment, events, protected seeking
- Worked well: Awaited initialization, packaged media, native overlay stacking and measured compositing
- Needs work: Empty HTTP error message; core manifest snippet omits player-session permission; delayed paused seek under load
- Onboarding zero → hello world: Builder Tools media workflow, explicit wants.service permissions and `/pkg/assets/raw/demo.mp4`; S5 measured actual frames
- Would build again: **Yes:** adapter keeps portable timing semantics and native playback isolated

## Amazon Devices Builder Tools MCP 1.0.15

- Used for: Installation/media/focus/storage/performance documentation and troubleshooting
- Worked well: Search and workflows identify API/manifest requirements
- Needs work: CLI lacks complete argument schemas; performance processor lookup failed despite installed SDK processor
- Onboarding zero → hello world: Pin npm package, list tools, supply `target_platform.device_os`; FL-001 gives working invocation
- Would build again: **Yes:** useful alongside native logs and official references

## Vega Perf CLI 0.24.0 / Appium 2.2.2 / Vega driver 3.30.0

- Used for: Native launch, focus, UI and video KPI runs
- Worked well: Native traces expose latency and dropped frames; direct bundled processor works
- Needs work: TTY requirement; scenario input can run before catalog readiness; absent fully-drawn KPI
- Onboarding zero → hello world: Install documented versions in task-local directories, doctor, record with TTY and passive prep; S6 preserves failed and valid reports
- Would build again: **Yes:** measurable evidence; clearer readiness and processor discovery would help

## AWS SAM 1.166.2

- Used for: Lint SAM policies and build the Lambda image
- Worked well: Local validation, clean-source build and container checks need no deployed stack
- Needs work: Its Docker builder did not reuse normal source-build cache
- Onboarding zero → hello world: Install pinned CLI, validate, build checksum-pinned release binaries; S7 records actual clean build
- Would build again: **Yes:** practical with pinned prebuilt artifacts

## Lambda Python 3.12 container / Docker 28.0.4

- Used for: Execute real H.264/H.265 analysis and publication on read-only root
- Worked well: `/tmp` configuration and minimal static decoder keep image under the measured budget
- Needs work: Original generic codec image exceeded budget; Lambda cloud timeout/cost remain unmeasured
- Onboarding zero → hello world: Start Docker, build, run actual encoded samples via `infra/check_image.py`; S7 preserves receipts
- Would build again: **Yes for packaging:** live AWS experience remains pending

## S3 / boto3 1.42.65

- Used for: SDK-compatible pipeline adapters: limits, ETags, pagination, retries and catalog concurrency
- Worked well: Conditional writes plus relisting preserve competing items
- Needs work: Listing alone permits stale catalog overwrites; real anonymous policy/latency untested
- Onboarding zero → hello world: Local integration fixtures, then `infra/smoke.py` when credentials/region exist
- Would build again: **Yes for the tested contracts:** no claim about live service onboarding

## ffmpeg / ffprobe 7.1.1

- Used for: Decode/synthesize tagged SDR, timestamps, pinned static container tools
- Worked well: Synchronized Y/RGB output, bounded grid and integer PTS
- Needs work: Release-specific rounded `pts_time`; official footage can omit color tags
- Onboarding zero → hello world: Probe an explicitly tagged clip, decode, compare flat-gray codes; S1 and S7 retain regressions
- Would build again: **Yes:** exact tagging and rational timing are essential

## GitHub / GitHub CLI

- Used for: Public reference repository, independent Linux CI and checksum-pinned wheel releases
- Worked well: Tagged CI enforces tests, schema and web contracts before publishing wheels
- Needs work: Existing Git credential and authenticated CLI identities differed
- Onboarding zero → hello world: Create public repo, use command-scoped authenticated credential helper, push tag and verify CI
- Would build again: **Yes:** independent source/build evidence

## Python / uv / NumPy / Numba / matplotlib / Pillow

- Used for: Typed engine, deterministic tests, numeric reports and nonflashing timeline GIF
- Worked well: Frozen contracts, strict types, source-keyed evidence and static reports
- Needs work: Solver workload and decoded cache storage are substantial; preserve real measured speed
- Onboarding zero → hello world: Locked environment, quality checks, encoded preflight then full evaluation
- Would build again: **Yes:** explicit numerical and provenance boundaries

## Firecrawl

- Used for: Official source/license page retrieval in S4
- Worked well: Direct official-source fallback completed acquisition
- Needs work: Exhausted credits produced HTTP 402 before retrieval
- Onboarding zero → hello world: Installed connector attempted official URLs; history records refusal and fallback
- Would build again: **Yes with credits:** no success is invented for blocked calls

**Vega Studio:** not used; installer skipped it because VS Code was absent. **Kiro:** not used. No onboarding or product rating is invented for either. Physical Fire TV hardware and live AWS Lambda/S3 were not exercised.
