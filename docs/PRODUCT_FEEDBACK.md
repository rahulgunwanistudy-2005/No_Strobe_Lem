# Product feedback — Session 1

Date: 2026-10-04. Host: macOS 26.3 (25D125), arm64. Lane A.

## Vega SDK and CLI

- Versions: SDK/VVD 0.24.12112; CLI 1.4.2. General tooling: Node.js 24.19.0; npm 11.17.0. The stock template install log used Node 22.11.0 / npm 11.10.0 and warned that react-native-kepler 4.0.1 requires Node ≥22.14.0. ffmpeg/ffprobe 7.1.1; uv 0.8.23; Python 3.12.11.
- Used the [official install guide](https://developer.amazon.com/docs/vega/0.24/install-vega-sdk), inspected the vendor installer, then ran `NONINTERACTIVE=true bash /tmp/nostrobe-s1-sources/get_vvm.sh`. It installed under `~/vega`, selected the SDK, and updated shell startup files. Required Homebrew utilities were installed. No global application code is copied into this repo.
- `vega --version` returned the versions above. `vega virtual-device start` returned `Virtual device ready`; `vega device list` showed an aarch64 VirtualDevice.
- Generated the stock template with `vega project generate --template helloWorld --name NostrobeHello --packageId com.nostrobe.hello --outputDir /tmp/nostrobe-s1-sources/hello`; `npm install`; `npm run build:app`. Build completed with exit 0 and produced all three architecture packages.
- Ran `vega run-app /tmp/nostrobe-s1-sources/hello/build/aarch64-release/nostrobehello_aarch64.vpkg com.nostrobe.hello.main -d VirtualDevice`. Device lifecycle check `vega exec vda shell vlcm list --app-id com.nostrobe.hello.main` confirmed `VISIBLE`, pid 4860. `vega virtual-device stop` completed; status reports `running:false`.
- Worked: official installation, CLI templates, cross-architecture build, run-app, device lifecycle inspection.
- Needs work: stock template install produced dependency deprecation/audit warnings and engine-version warnings; the stock build nevertheless succeeded. Review the template dependencies before S5. No dependencies were force-upgraded to hide these warnings.
- Vega Studio: installer skipped it because VS Code was not found; Studio was not required for the CLI hello-world gate.
- Onboarding: CLI route usable on this Mac; use `source ~/vega/env` before commands to avoid stale-path fallback warnings. Would build again: yes, subject to actual W3C media/compositing tests in S5.
- Limitation: the Mac was locked during desktop inspection, so no screenshot was captured. Device `VISIBLE` state is the run verification; no visual-layout claim is made.

## Amazon Devices Builder Tools MCP

- Package 1.0.15; configured in the local coding-agent MCP configuration as `amazon-devices-buildertools`, using pinned npm package and Node 24. No credentials needed. New server configuration may require a fresh chat/client reload to appear as callable tools in this chat.
- Verified through the package's documented CLI: `exec --list`, `exec list_documents --args '{"documentType":"WORKFLOW","target_platform":{"device_os":["vega"]}}'`, and `exec read_document --args '{"document_uri":"vega_sdk_installation.md"}'`. Read the SDK installation workflow; used the official web docs for concrete build/run command details.
- Worked: local documentation inventory and installation workflow retrieval. Needs work: CLI example `exec <tool-name> --args '{}'` does not expose required argument schemas; see FL-001. Would build again: yes; session-local tool availability still needs confirmation on reload.

## ffmpeg and numerical tooling

- Synthesizer uses limited-range YUV directly for luma, full-range BT.709 RGB for color, H.264 yuv420p CRF 10, explicit input/output and codec VUI tags.
- General output tag flags alone dropped transfer/primaries metadata on this host, while untagged input caused a two-code grayscale shift when converting to tagged output. Explicit matched input metadata and x264 VUI parameters resolve both; tested with ffprobe and flat-gray recovery.
- Downsampling signal values before linearization failed the hard-edge gate. Raised decode resolution to 640×360. Disabled psychovisual/adaptive quantization and capped QP at 6 to keep lossy synthetic encoding within the numerical fidelity gate.

W3C Media, Vega overlay animation, AWS, Kiro and physical Fire TV hardware were not exercised in S1; no feedback or measurements are invented for them.

## Session 2 — ffmpeg and numerical tooling

- Used ffmpeg/ffprobe 7.1.1 for 80 encoded smoke cases and the original 1080p
  Big Buck Bunny film; no playback was used. One input decoder splits Y and
  RGB into a synchronized raw stream shared by all three profile detectors.
  Independent Y/RGB decodes match this stream byte for byte.
- Worked: explicit source/output color metadata, shared PTS, bounded streams,
  source hashing, early cleanup and deterministic numerical traces. Non-BT.709
  color tags are refused for RGB analysis instead of silently converted using
  the wrong matrix/transfer.
- Profiling identified repeated table interpolation, spatial reduction and
  history traffic. Lookup tables, contiguous block sums, early area exits and
  frame-batched flash windows improved measured throughput. The final film run
  took 257.68 s (2.31× end-to-end); detector-only wall time was 122.68 s (4.86×).
  The 20× detection target is unmet. Concurrent test activity means timings are
  measurements on this host, not controlled isolated performance claims.
- Would build again: yes, with more profiling and an isolated benchmark before
  production ingestion. No new Vega/AWS/device-media claims are made in S2.

## Session 3 — numerical verification and reporting

- Used ffmpeg/ffprobe 7.1.1 to retain synchronized original code samples and PTS
  in source-keyed memory maps. NumPy computes blends before transfer/averaging;
  exact sample-history grouping avoids repeated identical cell work while
  preserving the original grid for global/local area rules.
- Worked: one decoder pass reused across candidate loops, no raw playback,
  source binding, continuous-ramp checks, explicit unresolved outputs, and
  self-contained Jinja2/matplotlib Agg reports inspected in the in-app browser.
- Needs work: real-content candidate search can be expensive. Original sample
  fidelity requires substantial disk cache space; timing/cost measurements
  belong in the S3 report. The final film run uses a warm cache and concurrent
  validation, so it cannot establish isolated cold-start performance.
- Would build again: yes; retain the full-file publication gate and profile
  truth distinctions while profiling candidate search. Vega overlay, measured
  synchronization/compositing and AWS were not exercised in this session.

## Session 4 — reproducible evaluation tooling

- Used ffmpeg/ffprobe 7.1.1, NumPy and matplotlib Agg for seeded encoded
  boundaries/shapes, explicitly tagged realistic composites and static control
  traces. No raw playback was used. Source checksums and official license
  snapshots make reference acquisition auditable.
- Worked: lossless compression of decoded sample bytes, bounded temporary
  extraction, repeat accuracy runs, separate retained timing observations,
  provenance invalidation and resumable evidence. Performance remains a
  measurement of this host with concurrent validation, not an isolated claim.
- Needs work: repeated candidate verification is expensive for spatially
  varied scenes. Older official movie releases omit source color metadata;
  strict input refusal is appropriate but narrows the unmodified control set.
- Composite encoding initially repeated the output-only metadata mistake:
  transfer/primaries tags were dropped. Matched raw-input tags and x264 VUI
  metadata resolved it; encoded-output metadata/color regression and actual
  five-scenario preflight now pass. Decoder checks remain strict.
- Firecrawl: official-page scrape requests were blocked by exhausted credits;
  the web reader also returned 402. Direct HTTPS worked. Would use again with
  available credits, retaining a direct official-source fallback.
- Would build again with the same deterministic pipeline and publication gate.
  Device synchronization/compositing and AWS remain unmeasured S5+ work.

## Session 5 — W3C playback and calibration

- SDK/VVD 0.24.12112, CLI 1.4.2, RN 0.83.0 / React 19.2.0,
  Kepler 4.0.1, W3C Media 2.3.2; macOS 26.3 arm64. Generated the current
  helloWorld template. Release and Debug builds succeed on aarch64/x86_64/armv7.
- Amazon Devices Builder Tools MCP worked directly in this session. Used
  project context, documentation inventory/search, the simple-media workflow,
  media API/surface initialization, manifest references and troubleshooting.
  Useful: headless player import, awaited initialization, module-version mapping
  and surface teardown guidance. The core manifest example omitted the
  player-session service that its reference table listed; runtime logs made
  that missing permission explicit. Search also confirmed the system audio
  service needed by D-pad focus sounds. Would use again: yes, with device-log
  verification of snippets.
- W3C URL playback rejects HTTP even on forwarded loopback, with native error
  code 4 and an empty message. JSON fetch over the same connection works.
  Amazon staff's local-asset guidance resolved media loading with literal
  `/pkg/assets/raw/demo.mp4`; startup now reaches loadedmetadata/canplay.
  The adapter surfaces a useful code-based error when the native message is
  empty. No insecure-protocol override was used.
- Remote input through inputd-cli worked: Enter triggered play/playing,
  advancing timeupdate events, ended, pause and seeked. After VVD restart the
  device-to-host port reverse must be reinstated. Dynamically preferred focus
  after controls become ready prevents startup focus from targeting disabled
  controls. Native playback logs are evidence of playback, not rendered UI QA.
- Native Animated setup produces no unsupported-driver error. Pixel-level
  opacity, relative surface stacking and actual timing remain unmeasured;
  there is no evidence to select a JS fallback yet. Native media also logs
  repeated no-time-update warnings at 11.999 s after emitting ended; the clock
  explicitly holds end-of-media. No unsupported end workaround was invented.
- SDK incremental staging retained removed Debug calibration raw assets in a
  subsequent Release package. A fresh generated Release staging tree resolves
  this; vpt package inspection confirms demo only in Release and three clips
  in Debug. JavaScript elimination alone is insufficient for raw-asset isolation.
- Capture blocker: host AVFoundation screen recording receives no frames
  (bounded retry after VVD restart); Finder inspection has no accessible
  window. Device screenshooter reports buffer permission failure/stalls and
  QMP screendump is black. Device capture attempts produced no valid stream.
  Recordings and calibrated engine parameters remain open. This is not a
  measured zero offset, a verified blend model or a native animation failure.
- The vendor template graph retains npm audit findings: 75 total (65 high,
  10 moderate), with an earlier production-only query reporting 42 (33 high,
  9 moderate; vendor packages also classify tooling as production dependencies).
  Root contract tooling audit returned zero. Ajv is pinned to 8.20.0. Avoided
  force-upgrading framework packages across the SDK's compatibility mapping.
  A later offline audit reported zero without fetching advisory data; that
  offline result is not used as a clean-security claim.
- Would build again: yes, but actual >=60 fps screen capture and measured
  RGB/limited-Y compositing are required before completing S5 or shipping a
  mitigation claim. No AWS, physical Fire TV or cloud work was exercised.


## S5 continuation — measured device loop

- The SDK-bundled, authenticated EmulatorController screenshot API resolved the
  capture blocker. Amazon staff’s VVD screenshooter limitation and the local
  SDK proto were more useful than QMP, which captured the wrong framebuffer.
  Actual pixels establish native Animated opacity above the video surface; no
  JS fallback is needed on this SDK/device combination.
- Counter-based observations prevented false measurements: package relaunch
  reused an existing process; a debug banner covered the pulse; high-rate
  capture plus host work introduced large delay; paused capture at one setting
  dropped below 60 fps. Reject those recordings, terminate between runs, use
  direct VDA input and reduce capture resolution/pace. Keep actual timestamps.
- The nine-case fit exposed RGB/limited-Y range confusion in the engine:
  original Y error 12.535 codes; corrected maximum RGB/Y errors 0.750/0.953.
  The largest scenario p95 determines the bound so steady sample count cannot
  dilute seek latency. Valid captures establish a 268.875 ms verifier tolerance.
- Release visual checks show video/veil/focus/disclaimer, refusal of failed
  tracks and a covered/stopped screen after background return. Initial paused
  native seek took about 4.8 s under concurrent host evaluation and retained a
  preroll image until Play. The app covers seeking and resumes at the target;
  startup/seek performance should be profiled separately on physical hardware.
- Would build again: yes. This resolves the S5 measurement blocker on VVD;
  it is not evidence for another SDK, display backend or physical Fire TV.

## S6 — TV UX and performance tools

- Builder Tools MCP supplied the focus guide, TVEventHandler, storage and
  performance workflows. A native focus guide fixed scrubber horizontal escape;
  border feedback and actual remote tests caught layout/scroll issues that Jest
  cannot establish. SDK captures provided readable actual pixels without a
  desktop lock/recording dependency.
- The RN 0.83 reference still endorses legacy core AsyncStorage while the SDK
  0.24 library guide recommends its replacement. The legacy API did not persist
  settings on this VVD; the RN 0.83 alias of the vendor AsyncStorage extension
  does, verified by native termination/relaunch. Cross-link/migrate those docs.
- The performance workflow's exact Appium/driver versions worked when installed
  in local isolated directories. `perf record` requires a TTY. MCP's processor
  lookup failed; the SDK's native processor and KPI Visualizer remained usable.
  Input latency lives in the debug JSON argument, not the trace slice duration.
- Preparation/start logging is not sufficient to infer when a scenario can
  send remote input. Wait for the post-launch catalog before Select. Terminating
  an app in the scenario's prep caused its selected process to be reported as
  crashed; discard that harness run, without claiming an application defect.
- Avoid timed tests alongside host-heavy builds. Retain missing video samples,
  frame drops and absent fully-drawn metrics rather than counting CLI exit zero
  as a performance pass. VVD performance cannot substitute for physical TV.
- Would build again: yes. Native D-pad, W3C, focus guide, storage and authenticated
  SDK screenshot capture support the full product flow. Better aligned storage
  docs, lifecycle-aware scenario readiness and self-contained trace-processor
  discovery would shorten onboarding.
