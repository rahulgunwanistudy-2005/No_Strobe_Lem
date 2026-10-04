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
