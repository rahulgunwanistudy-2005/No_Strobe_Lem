# No Strobe-lem on Vega

S5 provides a protected W3C player and a deterministic veil scheduler. It builds
and plays the bundled CC-BY demonstration on the Vega Virtual Device. Device
sync/compositing calibration is measured: ±268.875 ms verification tolerance,
with maximum blend errors of 0.750 RGB / 0.953 Y codes. See the
[S5 report](../docs/S5_REPORT.md) for recordings and fresh evaluation status.
The demo is a 12-second Big Buck Bunny opening excerpt checked numerically on
all three profiles. Its gentle cue demonstrates the overlay; it does not
represent a source hazard. No autoplay.

## Run the demonstration

Tested with Vega SDK/VVD 0.24.12112, CLI 1.4.2, React Native 0.83.0,
Kepler 4.0.1 and W3C Media 2.3.2 on macOS arm64. Use Node >=22.14.0.
From the repository root:

```sh
npm ci
cd tv
npm ci
npm run check:types
npm run typecheck
npm run lint
npm test
npm run build:release
cd ..
vega virtual-device start
vega exec vda reverse tcp:8765 tcp:8765
python3 -m http.server 8765 --bind 127.0.0.1 --directory tv/assets/raw
```

Keep the server running; in another terminal at the repository root:

```sh
vega run-app tv/build/aarch64-release/nostrobetv_aarch64.vpkg com.nostrobe.tv.main -d VirtualDevice
```

Select Play with the remote. Left/right selects the ±10-second controls;
Enter activates the focused control. Invalid, unresolved or mismatched
sidecars keep playback covered and disabled. Seek pauses playback, covers the
surface and primes the new veil before uncovering/resuming. Backgrounding
stops the player; reopen the app to continue.

`src/config.ts` configures the catalog server separately from the media path.
JSON uses the local forwarded server; W3C URL mode requires HTTPS or a local
package path. The bundled clip uses `/pkg/assets/raw/demo.mp4`. Reapply the
reverse mapping after restarting VVD. Only native platform files in `player/`
import Vega libraries. The generated types and standalone schema validator are
updated by `npm run gen:types`; `check:types` checks all generated outputs.

## Calibration lab

Instant calibration cues use a separate `production: false` descriptor. The
canonical HazardTrack loader refuses them. The Debug build includes the lab
and two stimuli; Release cleans SDK staging and excludes both MP4 files and
the lab module. Build through the package scripts so this exclusion holds.

Create a server directory from the committed, checksum-bound assets:

```sh
mkdir -p synth_out/s5/calibration
cp tv/assets/raw/demo.* synth_out/s5/
cp tv/calibration-assets/* synth_out/s5/calibration/
cd tv
npm run build:debug
cd ..
vega exec vda reverse tcp:8765 tcp:8765
python3 -m http.server 8765 --bind 127.0.0.1 --directory synth_out/s5
```

In another terminal, install `tv/build/aarch64-debug/nostrobetv_aarch64.vpkg`
with the same app id. Select Calibrate sync or Calibrate compositing, then
Play. Sync has a visible frame counter and a small one-frame patch every two
seconds; the veil switches at the same media timestamps. Compositing has a
static code ramp and nine three-second alpha/gray plateaus. Both encoded
stimuli have zero FAIL/WARN detector events on all profiles.

Capture the rendered VVD screen at >=60 fps (59.94 accepted), preserving
actual timestamps. Record sync separately during steady playback, seeks and
pause/resume; retain at least five paired flashes per scenario. Record the
full compositing sequence. Trim startup/exit frames outside visible media,
without retiming or frame duplication. Measure the exact video rectangle:
`--crop` is **width:height:x:y**, excluding controls and letterboxing. An
incorrect crop, missing counter/edges, low capture rate or bad baseline is
refused. An encoded stimulus resampled to 60 fps is not device evidence.

```sh
uv run --project engine python tools/measure_sync.py --recording /path/steady.mov --descriptor tv/calibration-assets/sync.json --scenario steady --crop W:H:X:Y --output synth_out/s5/steady.json
uv run --project engine python tools/measure_sync.py --recording /path/seek.mov --descriptor tv/calibration-assets/sync.json --scenario seek --crop W:H:X:Y --output synth_out/s5/seek.json
uv run --project engine python tools/measure_sync.py --recording /path/pause_resume.mov --descriptor tv/calibration-assets/sync.json --scenario pause_resume --crop W:H:X:Y --output synth_out/s5/pause_resume.json
uv run --project engine python tools/measure_sync.py --combine synth_out/s5/steady.json synth_out/s5/seek.json synth_out/s5/pause_resume.json --output engine/eval/sync_calibration.json
uv run --project engine python tools/measure_compositing.py --recording /path/compositing.mov --descriptor tv/calibration-assets/compositing.json --crop W:H:X:Y --output engine/eval/compositing_calibration.json
```

The sync report records signed offsets, each scenario’s absolute p95/max and
capture quantization. The combined p95 is the largest scenario p95; the pooled
p95 is retained separately so extra steady samples cannot dilute seek latency. The prescribed tolerance is `max(p95_abs * 1.5, 0.1)`; observed
outliers beyond it cause refusal. The compositing report fits captured RGB
codes and separately tests the corrected limited-Y code model using actual decoded
stimulus luma, retaining the original model error for comparison. A good RGB fit alone does not pass the engine
model gate. Retain recordings/checksums, investigate >2-code errors, apply
measured tolerance/model, then rerun the complete S3/S4 evaluation and update
its headline with the measured value. Current measurements and rerun evidence are linked in the S5 report.

To regenerate stimuli, use an available local TrueType font:

```sh
uv run --project engine python tools/generate_calibration.py --output synth_out/s5/calibration --font /path/font.ttf
```

Copy the new MP4/JSON pairs to `tv/calibration-assets/` and rebuild Debug;
font or encoder changes produce new hashes. `tools/prepare_demo.py --help`
describes reproduction from the checksum-pinned original film. See
[asset attribution](assets/README.md) and [measurement status](../engine/eval/s5_calibration_status.json).


## SDK capture fallback used in S5

AVFoundation yielded no frames on this host. The installed VVD’s authenticated
`EmulatorController.getScreenshot` API returns actual rendered pixels. Use the
SDK’s `emulator_controller.proto` and existing emulator discovery file; the
recorder never prints or saves the authentication token. Enable the local gRPC
endpoint through the authenticated emulator console and keep it on loopback.
The installed proto is under `vvd/images/tv/vmtools/agent/lib/`; discovery files
are under `~/Library/Caches/TemporaryItems/avd/running/` on this host.

Before each run, terminate the previous application instance, then launch it:

```sh
vega exec vda shell vlcm terminate-app --pkg-id com.nostrobe.tv
vega device launch-app --appName com.nostrobe.tv.main
```

Reinstalling the same package may reuse its process and old playback position.
Use the direct executable returned by `vega which vda` for timed remote input;
this avoids the host CLI’s startup cost. Select the lab, wait for its paused
player, then start playback and acquisition. Analyze after acquisition to keep
host contention down. Capture dimensions may be reduced for sync while keeping
the patch/counter readable; require actual average and median rates >=59.9 fps.

```sh
env -u PYTHONPATH uv run --no-project --with grpcio==1.76.0 --with grpcio-tools==1.76.0 python tools/capture_vvd.py --proto-dir /absolute/sdk/proto/directory --discovery /absolute/pid-discovery.ini --output synth_out/s5/captures/run --duration 31 --width 960 --max-fps 110
ffmpeg -v error -f concat -safe 0 -i synth_out/s5/captures/run/frames.ffconcat -fps_mode passthrough -enc_time_base 1:1000000 -c:v ffv1 -level 3 -pix_fmt gbrp -threads 1 synth_out/s5/captures/run.mkv
```

The rate option paces requests; it never assigns nominal timestamps or creates
frames. SDK timestamps remain in `capture.json`. The accepted S5 recordings
have 11,070 real samples; FFV1 timestamps differ from the original timestamps
by at most 0.5 ms. Exact crops, rates, hashes and remote input observations are
in `docs/evidence/s5/capture_provenance.json`. At 960×540 the lab video crop is
`770:434:94:0`; at 640×360 it is `514:289:63:0` on this layout. Re-measure after
layout/device changes. Native paused seek can keep the previous/preroll image
until Play; the clock and target veil are primed before playback resumes.

The analyzer requires an actual source-counter jump for a seek run and an
interior frame hold for pause/resume. A flash already covered at its exact
seek frame is retained as pixel coverage evidence, with no invented onset
offset. Every scenario still requires at least five distinct timed onsets.
Debug-only filters remove the vendor forwardRef warning and SDK startup/warning
banners from the video; underlying device logs and playback errors remain.
