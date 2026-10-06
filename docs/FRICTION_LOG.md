# Friction log

Consolidated distinct reproduced issues; no entry is added to satisfy a count. Original observations, commands and rejected attempts remain in [FRICTION_HISTORY.md](FRICTION_HISTORY.md). S5/S6/S7 evidence directories retain runtime artifacts.

### FL-001 — CLI tool execution hides required argument schema
- Product / tool: Amazon Devices Builder Tools MCP CLI
- Date / version: 2026-10-04; 1.0.15; Node 24.19.0; macOS 26.3 arm64
- Task attempted: Retrieve installation workflows using the documented CLI `exec` route.
- Steps taken: 1. `npx -y @amazon-devices/amazon-devices-buildertools-mcp@1.0.15 --help`; 2. `npx -y @amazon-devices/amazon-devices-buildertools-mcp@1.0.15 exec --list`; 3. `npx -y @amazon-devices/amazon-devices-buildertools-mcp@1.0.15 exec list_documents --args '{"documentType":"WORKFLOW"}'`.
- Expected: Tool list/help exposes a complete input schema or a valid invocation example.
- Actual: `Schema validation failed: data must have required property 'target_platform'`. Follow-up validation establishes it is an object requiring an array `device_os`. The help lists tool descriptions but no argument schemas.
- Severity: Minor
- Workaround: `--args '{"documentType":"WORKFLOW","target_platform":{"device_os":["vega"]}}'` retrieves the workflow inventory. `read_document` uses `document_uri`, not `name`.
- Suggestion: Add `exec <tool> --schema` and print required argument types plus an example on validation failure.

### FL-002 — W3C player-session permission omitted from core snippet
- Product / tool: W3C Media 2.3.2 / SDK 0.24.12112 / CLI 1.4.2
- Date / version: 2026-10-05; macOS arm64
- Task attempted: Initialize the installed player
- Steps taken: 1. Install and run the S5 app. 2. `vega exec vda shell loggingctl log -v com.nostrobe.tv`.
- Expected: VideoPlayer can connect using the documented core manifest.
- Actual: Native log: missing permissions for `com.amazon.media.playersession.service`.
- Severity: Major
- Workaround: Declare that wants.service from the reference table and rebuild.
- Suggestion: Include player-session permission in the core media example.

### FL-003 — Loopback HTTP media refuses with empty error
- Product / tool: W3C Media 2.3.2 / VVD 0.24.12112
- Date / version: 2026-10-05; macOS arm64
- Task attempted: Play the local demo URL
- Steps taken: 1. Forward `vega exec vda reverse tcp:8765 tcp:8765`. 2. Launch the S5 Release using its local HTTP catalog. 3. Inspect `loggingctl log -v com.nostrobe.tv`.
- Expected: Supported URI requirements and a useful error message.
- Actual: JSON fetch succeeds, MP4 playback rejects insecure HTTP; code 4, empty native message.
- Severity: Major
- Workaround: Use documented `/pkg/assets/raw/demo.mp4`; no TLS bypass.
- Suggestion: Document URI restrictions at src and provide explanatory native errors.

### FL-004 — Incremental Release retains removed calibration assets
- Product / tool: Vega SDK 0.24.12112 / CLI 1.4.2
- Date / version: 2026-10-05; macOS arm64
- Task attempted: Exclude calibration media from Release
- Steps taken: 1. Build Debug, move calibration source assets out, then build Release. 2. `vega exec vpt show-contents` on the resulting package.
- Expected: Removed source assets are absent.
- Actual: Release still contains `assets/raw/sync.mp4` and `compositing.mp4`.
- Severity: Major
- Workaround: Build wrapper cleans generated Release staging; inspect package contents.
- Suggestion: Delete stale raw-asset staging entries during incremental packaging.

### FL-005 — Screen capture paths return unavailable or wrong framebuffer
- Product / tool: VVD/SDK 0.24.12112 / ffmpeg 7.1.1
- Date / version: 2026-10-05; macOS arm64
- Task attempted: Capture actual playback for timing
- Steps taken: 1. `ffmpeg -f avfoundation -framerate 60 -i '1:none' -t 1`. 2. Device screenshooter and QMP capture attempts, recorded in S5 provenance.
- Expected: Rendered frames with acquisition timestamps.
- Actual: AVFoundation emits no frames; screenshooter permission/stall; QMP entirely black.
- Severity: Blocker
- Workaround: Authenticated SDK EmulatorController.getScreenshot; reject unusable captures.
- Suggestion: Expose a supported timestamp-preserving VVD capture command.

### FL-006 — Remote focus sound needs another manifest service
- Product / tool: SDK 0.24.12112 / CLI 1.4.2
- Date / version: 2026-10-05; macOS arm64
- Task attempted: Navigate focus using D-pad
- Steps taken: 1. Run S5 Release. 2. Send D-pad input. 3. Inspect `loggingctl log -v com.nostrobe.tv`.
- Expected: Core audio manifest covers focus sounds.
- Actual: Volta UISoundManager cannot connect to `com.amazon.audio.system`.
- Severity: Minor
- Workaround: Add documented system-audio wants.service and rebuild.
- Suggestion: Include focus/system-sound permission in TV media templates.

### FL-007 — CLI-ready VVD dies with parent session
- Product / tool: Vega SDK 0.24.12112 / CLI 1.4.2
- Date / version: 2026-10-06 IST; macOS arm64
- Task attempted: Start a persistent test device
- Steps taken: 1. `vega virtual-device start`. 2. Let invoking session close. 3. `vega virtual-device status`; `vega device list`.
- Expected: A reported ready device remains available.
- Actual: Twice: ready message, then running=false and no device.
- Severity: Major
- Workaround: Keep launch terminal alive and independently verify device discovery.
- Suggestion: Detach emulator lifetime or report parent-session ownership explicitly.

### FL-008 — Settings core API loses preferences after restart
- Product / tool: Kepler 4.0.1 / RN 0.83 / SDK 0.24.12112
- Date / version: 2026-10-06 IST; macOS arm64
- Task attempted: Persist Kids household and warnings Off
- Steps taken: 1. Select Kids/Off on installed Release. 2. `vega exec vda shell vlcm terminate-app --pkg-id com.nostrobe.tv`. 3. Relaunch without reinstall, open Settings.
- Expected: Saved choices survive process restart.
- Actual: Legacy core AsyncStorage returns without error, but restores Family/Broadcast/On.
- Severity: Major
- Workaround: Use pinned SDK AsyncStorage extension; native restart repeat passes.
- Suggestion: Align RN storage docs with SDK replacement and compatibility map.

### FL-009 — Performance processor discovery and TTY requirements
- Product / tool: Vega Perf CLI 0.24.0 / SDK 0.24.12112 / Builder Tools 1.0.15
- Date / version: 2026-10-06 IST; macOS arm64
- Task attempted: Record/analyze native performance
- Steps taken: 1. Invoke perf recording without TTY. 2. Analyze recorded traces through Builder Tools MCP. See S6 raw reports and history.
- Expected: Documented record/analyze route finds installed components.
- Actual: Record errors `(19, Operation not supported by device)`; MCP cannot locate installed trace processor.
- Severity: Major
- Workaround: TTY controls record; invoke SDK-bundled processor directly with query files.
- Suggestion: Detect missing TTY early and discover processor from the selected SDK.

### FL-010 — Human-readable PTS precision changes across releases
- Product / tool: ffmpeg 7.1.1 / GitHub Ubuntu 24.04 ffmpeg
- Date / version: 2026-10-06 IST; macOS and Ubuntu
- Task attempted: Run unchanged must-pass boundary tests
- Steps taken: 1. Push extracted library CI. 2. `uv run pytest -q` on Ubuntu; compare macOS. Failed runs linked in history.
- Expected: Identical six-change windows at 24/30/60 fps.
- Actual: Rounded `pts_time` admits an extra change; three unchanged tests fail on Linux.
- Severity: Major
- Workaround: Use integer PTS and rational filter time base; invalidate prior caches.
- Suggestion: Use exact timestamp fields in decoder integrations; document pts_time precision.

### FL-011 — Git and CLI credential identities differ
- Product / tool: GitHub CLI / existing HTTPS credential helper
- Date / version: 2026-10-06 IST; macOS arm64
- Task attempted: Push newly created public reference repo
- Steps taken: 1. `gh repo create rahul-software-dev/hazardtrack --public`. 2. HTTPS push from extracted repository.
- Expected: Push uses the account that created the repository.
- Actual: Existing Git credential is another account; HTTP 403.
- Severity: Major
- Workaround: Command-scoped gh auth git-credential helper; no global credential changes.
- Suggestion: Surface Git-versus-CLI identity mismatches without printing tokens.

### FL-012 — SAM source build does not reuse ordinary Docker cache
- Product / tool: SAM 1.166.2 / Docker 28.0.4
- Date / version: 2026-10-06 IST; macOS arm64
- Task attempted: Build the already tested Lambda image through SAM
- Steps taken: 1. Complete ordinary Docker source build. 2. `sam build --template-file infra/template.yaml`.
- Expected: Normal builder can reuse the existing expensive source compilation.
- Actual: SAM repeats AL2023 bootstrap/configure; attempt deliberately stopped.
- Severity: Major
- Workaround: Publish source/licensed, checksum-pinned static binaries; clean SAM build then passes.
- Suggestion: Document builder cache isolation and artifact packaging for compiled dependencies.

## S8 security follow-up

The official npm advisory endpoint reports unfixed `braces` stack exhaustion in the dependency graph; the initial legacy `toml` findings were fixed in the SDK dependency graph. Supported Lodash/Minimatch/Ajv updates were applied and tested; remaining findings retain their exact reports in `docs/evidence/s8/`. No offline audit is treated as proof of security.
