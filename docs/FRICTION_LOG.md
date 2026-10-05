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
