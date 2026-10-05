# S5 rendered-device evidence

Actual VVD samples on SDK 0.24.12112, not mockups. The application only played
checksum-pinned, verified CC-BY demo/calibration content. Authentication tokens
are absent from evidence. Capture/provenance is in capture_provenance.json;
measurement matrices are in engine/eval/sync_calibration.json and
engine/eval/compositing_calibration.json.

- demo_paused_veil.png: Release, remote Play then Pause inside the gentle veil;
  visible video, focus ring, title, controls and complete disclaimer.
- compositing_rendered.png: actual frame 333 from the unobscured recording;
  source counter and alpha 0.25 / gray 0.5 plateau above the video surface.
- refused_track.png: actual deliberately failing verifier fixture, covered
  video and disabled controls. The server sidecar was restored byte-for-byte.
- background_return.png: actual background/foreground transition, stopped
  native player and covered screen; fresh restart succeeds.
- seek_paused.png: actual +10 s initial paused seek, black shield while native
  seek was pending. SDK logs later emitted seeked after ~4.8 s; Play resumed
  at the target and ended after the remaining excerpt. No preview-latency claim.
- release_contents.txt / debug_contents.txt: rebuilt package inventories;
  calibration clips exist only in Debug. S5_VALIDATION.json has all six hashes.

The shared scheduler fixture verifies seek into a veil and end-of-media in
500 sample times. The actual sync seek recording also exposes its frame-240
pulse under the already-full target veil: background 88, patch 181 display
codes. That covered flash is listed separately from the eight timed onsets.

Recordings and original per-frame SDK timestamps remain locally in ignored
synth_out/s5/captures/. The accepted four recordings have 11,070 actual samples;
no interpolation, synthesized frames or nominal-rate retiming was used. The
lossless FFV1 encode preserves count and timestamps to within 0.5 ms. Low-rate,
obscured, stale-instance and overloaded attempts were rejected and retained
locally as diagnostics. The original compositing error is retained separately
in engine/eval/audits/s5_original_compositing_model.json.
