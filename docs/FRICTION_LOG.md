# Friction log

Entries below describe reproduced issues only. SDK availability and test results are recorded in PRODUCT_FEEDBACK.md.

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

## Session 2 update — 2026-10-04

Standards PDFs were readable and the combined ffmpeg Y/RGB stream matched
separate decodes byte for byte. No new external-tool blocker was reproduced.
The detection throughput target remains unmet; profiling and measured results
are recorded in S2_REPORT.md and s2_benchmark.json as an implementation
limitation, rather than attributed to a vendor without evidence.

## Session 3 update — 2026-10-04

No new external-tool blocker was reproduced. Repeated verification on the
encoded area cases was slow, so exact sample-history grouping was added:
byte-identical cell histories share change counters, then counts expand back
to the original grid for global/local area decisions. Equivalence checks use
exact array equality and all-profile event equality. This is an implementation
optimization, not vendor friction. The first film cache preparation completed;
that analysis was interrupted during development, so the recorded final film
benchmark explicitly starts with a warm decode cache. Concurrent validation
activity is recorded rather than presenting the timing as an isolated run.

## S4 source access — 2026-10-05

- Firecrawl scrape calls to official Blender license/download pages returned
  `Insufficient credits`; the web reader returned HTTP 402 on the same URLs.
- Reproduction: Firecrawl scrape with `maxAge: 0` for
  `https://peach.blender.org/about/` and `https://mango.blender.org/sharing/`.
- Workaround: direct HTTPS retrieval succeeded with curl; license snapshots
  are retained under `engine/eval/sources/`. No source facts were invented.

## S4 untagged reference releases — 2026-10-05

ffprobe 7.1.1 reports no color_transfer/color_primaries/color_space for the
Blender-hosted Tears of Steel 720p MOV, ToS-4k-1920 MOV, and Sintel 1080p
trailer MP4. The strict probe rejects them with `unsupported or unspecified
transfer: unknown`. Reproduced via ffprobe stream color metadata fields.
No detector checks were weakened. Retained the explicitly BT.709-tagged
Big Buck Bunny original as the full-film control; Tears of Steel is only
an artistic background to explicitly tagged synthetic composites.

## Detection performance follow-up — 2026-10-05

An attempted transposed RGB-to-XYZ matrix multiplication preserved most test
values but changed some 9×12-grid values by up to 1.11e-16. Reproduced with
`engine/tests/detect/test_equivalence.py` against the frozen dd980e5 reference.
The change was rejected; original NumPy matrix multiplication and strict
compiled arithmetic preserve exact measured state and event output. This is
an implementation/numerical issue, not external-tool friction.

## S5 W3C player-session permission — 2026-10-05

SDK 0.24.12112, CLI 1.4.2, W3C Media 2.3.2. The Builder Tools media
player document lists player-session service in its reference table but omits
it from the core manifest snippet. The first installed app reached VISIBLE
(pid 5960), but `vega exec vda shell loggingctl log -v com.nostrobe.tv` showed
`Unable connect to 'com.amazon.media.playersession.service'. Missing the
permissions needed to connect to the service.` Added that explicit wants
service before the next build; no platform security checks were disabled.

## S5 desktop recording unavailable — 2026-10-05

`ffmpeg -f avfoundation -framerate 60 -i '1:none' -t 1` listed screen capture
but received no frames and did not complete. Stopped the capture process.
Computer-use Finder inspection returned `cgWindowNotFound`; the bare VVD
executable was not an addressable app. The Mac may be locked (not proven).
Asked the user to make the desktop available. Device `screenshooter` also
reported buffer-file `Permission denied`; its Wayland request stalled. These
are capture blockers, not measured timing or unsupported native animation.

## S5 direct URL playback requires a secure URI — 2026-10-05

The local catalog/JSON requests over the forwarded loopback server succeeded,
but W3C URL mode refused its HTTP MP4 URI. Reproduced on VVD with the release
app and loggingctl: `isUriSchemeSecure Got an insecure protocol/scheme http,
return error`, followed by media error code 4 (empty native message).
The reader's protective cover held. Investigating packaged local assets for
the short nonhazardous demo; no insecure-protocol override or TLS bypass.

Packaged local playback resolved the HTTP refusal using the Amazon-documented
`/pkg/assets/raw/demo.mp4` path. Runtime logs now show duration 12000 ms,
loadedmetadata and canplay; source/surface initialization is functional.
Reference: https://community.amazondeveloper.com/t/proper-uri-handling-for-local-assets-in-kepler-toastkepler-and-w3c-media-video/27642

## S5 incremental packaging retains removed raw assets — 2026-10-05

A Release build after moving calibration stimuli out of the source assets
still contained `assets/raw/sync.mp4` and `assets/raw/compositing.mp4` according
to `vega exec vpt show-contents`. The SDK copied new assets but retained old
staging files. The build wrapper now starts Release with a fresh generated
build directory, then includes calibration MP4 files only during Debug.
Package contents are checked separately from JavaScript dead-code removal.

## S5 system audio permission — 2026-10-05

Remote D-pad focus invoked Volta UISoundManager and failed to connect to
`com.amazon.audio.system`: missing wants.service declaration. The initial
manifest already included stream/control audio services. Builder Tools
search confirmed the system-audio requirement for focus/system sounds;
added it and rebuilt both package modes. No privilege or security override.

The post-restart recording retry was bounded to ten seconds and killed when
AVFoundation still provided no usable frames. QMP's successful screenshot
request returned an entirely black framebuffer, which was rejected as visual
and calibration evidence. A VVD restart also clears port reverse mappings;
reapplying `vda reverse tcp:8765 tcp:8765` restored catalog loading.

## S5 continuation: supported capture and vendor warning — 2026-10-05

Amazon staff confirm gwsi-tool-screenshooter is unsupported on VVD. The
SDK-bundled EmulatorController.getScreenshot API, enabled through the local
emulator console and authenticated with its existing discovery token, yields
actual 1920×1080 rendered screenshots. The endpoint listens only on loopback;
no token is printed, committed or authentication disabled. QMP was capturing
a different framebuffer. Host AVFoundation remains unavailable.

The Debug image exposed React's forwardRef arity warning over the video.
W3C Media 2.3.2's bundled source map identifies SliderMetaData's one-argument
forwardRef callback. Ignore only that exact vendor warning in Debug LogBox
so it cannot contaminate calibration pixels; retain other diagnostics.
Initial capture attempts below 60 fps are rejected. Sampling and encoding
are measured separately; protobuf image bytes must be cached once rather
than accessed for every row (each property access copies the full frame).

- Reinstall/launch of the same package can foreground an existing process rather
  than reset it. Frame counters exposed this: a supposed fresh pause/resume run
  began at frame 228 and only yielded four timing pairs; it was rejected. Use
  `vlcm terminate-app --pkg-id com.nostrobe.tv`, then launch a new instance and
  verify a fresh paused player and initial source position before recording. Invoke the SDK's direct
  vda executable during recordings to avoid repeated host CLI startup overhead.
- Unpaced screenshot polling plus host work delayed a seek-run onset beyond
  500 ms. Pace acquisition with original timestamps and perform
  heavy analysis after capture. Retain the rejected recordings as diagnostics.

- The 75-request/s setting achieved only 45.469 fps in one paused run. It was
  rejected. Reducing sync acquisition to 640×360 with a 110-request/s ceiling
  produced 96.648 actual fps; the capture retains timing jitter and does not
  duplicate frames. Larger requested rate is only a ceiling, not evidence.
- React Native’s generic “Open debugger to view warnings” banner and the SDK’s
  “Running debug build of JavaScript” notification remained after filtering the
  forwardRef warning. Filter those exact Debug notifications too; native logs
  retain diagnostics and actual exceptions remain visible. Repeat the captures
  with the patch unobscured; do not infer timing through the banner.
- Initial paused native seek returned seeked after ~4.8 s while host evaluations
  were running. Preroll remained black until Play, then the excerpt ended at the
  requested target’s remaining duration. The app’s black seek shield remained
  present during the wait; this is functional evidence, not a latency benchmark.

## S6 — virtual-device launch lifetime (2026-10-06 IST)

- Tool/version: Vega SDK 0.24.12112, CLI 1.4.2, macOS arm64.
- Reproduction: `vega virtual-device start` (also `--no-gui`) reports
  'Virtual device ready'; immediately after the invocation completes,
  `vega virtual-device status` reports running=false and `vega device list`
  reports no devices. Reproduced twice. Performance doctor consequently
  reports 'No supported devices found'.
- Expected: the device remains available for install, remote and capture checks.
- Impact: CLI readiness alone cannot establish an S6 device gate.
- Investigation: keep the launch terminal open to distinguish session lifetime
  from an emulator failure. Outcome recorded in the S6 report.

## S6 — performance tooling prerequisites and trace fallback (2026-10-06 IST)

- Vega Perf CLI 0.24.0 initially reports Appium absent. Installed the documented
  Appium 2.2.2 / Vega driver 3.30.0 in ignored, task-local directories; no global
  installation or existing tool removal. The generated scenario uses official
  `jsonrpc: injectInputKeyEvent` select code 96.
- `perf record` without a TTY errors `(19, 'Operation not supported by device')`.
  A terminal plus its documented `s`/`q` controls records actual traces.
- Builder Tools `analyze_perfetto_traces` cannot find its trace processor even
  though local `vega exec perf` works. Used the SDK-bundled processor directly.
  Its `-q` flag takes a file; multiple result-producing statements require
  separate queries. Both errors were reproduced, then corrected.
- Initial 40-second UI/player trace includes concurrent screenshot/input work:
  native last-input latency spans 21–223 ms and dropped UI-frame counters are
  nonzero. Retained as diagnostic evidence, not a zero-drop gate. Repeated
  unchanged opacity writes were removed before the final measurement.
- Three launch runs return real TTFF values but their combined validator fails
  because TTFD is absent. S6 does not label that report a complete KPI pass.

## S6 — legacy settings did not survive process restart (2026-10-06 IST)

- Core Kepler AsyncStorage returned without a visible error, but selecting Kids
  household and warnings Off, terminating with `vlcm terminate-app`, launching
  the same installed package and opening Settings restored Family/Broadcast/On.
  Reproduced on a fresh Release install with no intervening reinstall or VVD reboot.
- The React Native 0.83 AsyncStorage page recommends the core stopgap; the SDK
  0.24 library page instead recommends its autolinked AsyncStorage extension.
  Migrated to the documented RN 0.83 npm alias, pinned to 2.1.9000000001, whose
  compatibility map targets IAsyncStorage__AsyncStorage_1. Repeat the exact
  native restart test; unit mocks alone cannot establish persistence.
- The first final Jest run overlapped a native build and timed out finding the
  catalog. The isolated test passed without changing its assertion or timeout;
  the later full 46-test run passed. Keep host-heavy builds out of timed checks.
- Attribution inherited Settings' scroll offset, hiding its Back control.
  Reset the scroll position when changing views; the disclaimer remains a
  D-pad focus destination. Catalog posters were reduced to keep card focus
  borders visible on the 1080p TV viewport.

- Constant Kids cue initially displayed opaque gray: cached opacity was sent
  before native zero-duration initialization completed, allowing its final 1
  to overwrite the cue. Await native completion before rAF priming; add a
  regression for completion ordering, constant-target caching and teardown.

## S6 — performance scenario readiness

- The first video run completed three iterations but only one produced video
  KPIs; Select was sent immediately after native launch, before the catalog was
  necessarily focusable. Discard the aggregate as repeated video evidence.
- A trial reset inside prep terminated the process selected by the KPI runner,
  which reported a crash with no crash log; that harness run was interrupted
  and is not application crash evidence. Keep prep passive and wait three
  seconds after launch in run before remote Select; measure again exclusively.
- Rapid manual termination/relaunch can return status 255. A bounded lifecycle
  settling interval and tolerating “not running” termination allowed the
  remaining error-state checks to complete. All temporary fixture bytes restored.
- The supported AsyncStorage extension retained Kids/Off across native restart;
  the repeat on the final Release passed. Constant Kids veil now shows video
  rather than opaque gray after the initialization-order fix.

- Corrected final video scenario produced three usable iterations: 18.4–19.6
  fps for the 24-fps excerpt, 76.7–81.7% fluidity, first video frame
  923.4–1376.4 ms. Consecutive dropped-frame metrics remain nonzero. The
  zero-drop gate is not met; this VVD result is not a physical-TV estimate or
  proof that the rAF loop caused every drop. Preserve the raw reports/traces.

## S7 — timestamp precision differs across ffmpeg releases

GitHub Ubuntu 24.04 CI (`uv run pytest -q`) reproduced three unchanged S1
must-pass failures at exactly 3 flashes/s (24/30/60 fps). Local macOS ffmpeg
7.1.1 passed the same 419 extracted tests. CI logs show event boundaries such
as 1.33333 s: the decoder consumed rounded `showinfo pts_time`, allowing one
extra change inside the trailing window. Resolution: consume integer `pts`
and the filter's rational time base, add exact-boundary timestamp regressions,
and bump the decoded-cache version. No ground truth or threshold was changed.
Failed runs: https://github.com/rahul-software-dev/hazardtrack/actions/runs/37439088441
and https://github.com/rahul-software-dev/hazardtrack/actions/runs/37439231961.

## S7 — build tooling and image budget

Initial `uv tool install aws-sam-cli` and infra dependency downloads timed out,
including botocore/awscrt wheel extraction; explicit 180 s HTTP timeouts and a
retry using the official PyPI index completed installation (SAM 1.166.2).
Docker 28.0.4 was installed but its daemon was stopped; launching Docker resolved
that. The initial Lambda Python 3.12 + general-purpose static LGPL ffmpeg image
measured 1,224,378,400 bytes, above the <1 GB target. Packaging switches to an
official checksum-pinned ffmpeg source build restricted to the pipeline's
MP4/H.264/H.265 decoding and raw-output filters; final measurements follow in
S7_REPORT.md. AWS configuration reports no access key/profile/region, so no
cloud duration, cost, public-access or teardown result is claimed.

## S7 — GitHub CLI and Git credential identities differ

`gh repo create rahul-software-dev/hazardtrack --public` succeeded, but an HTTPS
push used the existing rahulgunwanistudy-2005 Git credential and returned 403.
A command-scoped `gh auth git-credential` helper pushed through the authenticated
rahul-software-dev account. No global credential setting or token was changed
or committed.

## S7 — SAM and Docker build caches differ

`sam build --template-file infra/template.yaml` used Docker's separate build
path and did not reuse the successful source-compilation layer from `docker
build`. Its AL2023 package bootstrap/configure stage repeated the slow network
and emulation work. That validation attempt was stopped deliberately. Resolution:
publish the already tested minimal static binaries as a versioned release
bundle, including their official source archive, LGPL license, exact build
recipe and provenance; pin its actual SHA-256 in the normal Dockerfile. Keep
`Dockerfile.source` for independent rebuilding. No detector or quality gate was
removed; the final clean SAM/image checks use the downloaded, checksum-verified
artifact.
