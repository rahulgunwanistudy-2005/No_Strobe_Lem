# Hard questions → answers

**"Does this work on Netflix / Prime Video?"** Not today: third-party apps can't read other apps' frames, by design. HazardTrack is a format; the path to every app is the platform player consuming it, the way captions work. Our app is the reference implementation; the spec and library are open.

**"Detection already exists (Harding, PEAT, Flikcer)."** Agreed, and we say so. We contribute the carrier and the proof: a versioned sidecar any player can apply, and mitigation verified against the same rules under measured sync error.

**"Isn't dimming the screen a bad experience?"** It only happens inside hazardous segments, ramps in over half a second, and is the minimum strength that passes. Measured: {{veiled_pct}}% of runtime, mean strength {{mean_alpha}}. Viewers who prefer can skip instead.

**"Can the veil itself cause a flash?"** No: ramps are ≥ 0.5 s, nearby veils are merged within 1 s, and the verifier checks the veiled output including ramps.

**"What if sync slips on a real device?"** Tolerance is measured, not assumed: {{tol_ms}} ms (p95 × 1.5) from screen recordings on the Vega Virtual Device. Every published track passes at both extremes. Segments that can't be fixed within the maximum veil are marked unresolved and default to a skip prompt.

**"Why not deep learning?"** The standard is rule-based and broadcasters audit against it. Deterministic rules give reproducible, explainable verdicts; our eval re-runs byte-identical.

**"How do you know you're correct?"** Synthetic clips with analytic ground truth at every rule boundary (rate, area, ΔL, the 160 cd/m² regime switch, 9-frame spacing, red chromaticity), multiple frame rates, realistic hazards composited onto CC-BY footage, and clean films as a false-positive control. Zero missed hazards on {{n_fail}} must-fail clips. {{PEAT agreement if run}}.

**"Medical claims?"** None. It's a viewing aid aligned to broadcast guidelines; disclaimer in app, README and here.

**"HDR? Live?"** SDR VOD in v1. BT.1702-3 defines PQ/HLG curves; live needs a look-ahead buffer. Both on the roadmap.

**"Why Vega?"** It's Amazon's new TV OS, it's React Native, and its W3C media API let us keep playback semantics identical between the web reference reader and the TV.

**"What does AWS do here?"** Turns publishing into one upload: S3 → Lambda analysis for all profiles → verified tracks, report and catalog, at ${{cost_per_hour}} per hour of video.
