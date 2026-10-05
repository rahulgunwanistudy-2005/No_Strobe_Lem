# No Strobe-lem on Vega

S5 provides a protected W3C player and a deterministic veil scheduler. It builds
and plays the bundled CC-BY demonstration on the Vega Virtual Device. Device
sync/compositing calibration is **pending**; see [S5 report](../docs/S5_REPORT.md).
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

The sync report records signed offsets, absolute p95/max and capture frame
quantization. The prescribed tolerance is `max(p95_abs * 1.5, 0.1)`; observed
outliers beyond it cause refusal. The compositing report fits captured RGB
codes and separately tests the engine's original limited-Y code model using
actual decoded stimulus luma. A good RGB fit alone does not pass the engine
model gate. Retain recordings/checksums, investigate >2-code errors, apply
measured tolerance/model, then rerun the complete S3/S4 evaluation and update
its headline with the measured value. That final gate has not been performed.

To regenerate stimuli, use an available local TrueType font:

```sh
uv run --project engine python tools/generate_calibration.py --output synth_out/s5/calibration --font /path/font.ttf
```

Copy the new MP4/JSON pairs to `tv/calibration-assets/` and rebuild Debug;
font or encoder changes produce new hashes. `tools/prepare_demo.py --help`
describes reproduction from the checksum-pinned original film. See
[asset attribution](assets/README.md) and [measurement status](../engine/eval/s5_calibration_status.json).
