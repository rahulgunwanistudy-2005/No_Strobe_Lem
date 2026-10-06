# Build and demonstration safety

No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.

The Release player waits for a matching verified HazardTrack and an initialized native surface/veil before autoplay. Invalid, mismatched, failing or unresolved tracks keep the player covered and disabled. Missing analysis stays paused; an explicit unprotected choice retains a visible banner and does not autoplay. Kids focuses the keep-paused choice. This behavior is a documented product interpretation, not an assurance about unknown media.

Protected seeking pauses playback, covers the surface, serializes remote inputs, primes destination timing and waits for veil propagation before resuming. Native seek errors keep the cover and offer retry. Backgrounding stops playback and requires retry. Runtime failures do not convert to an unprotected mode.

Synthetic hazard clips use `HAZARD_` filenames under ignored `synth_out/`, accompanied by a warning README. Never autoplay them or commit raw stimuli. Photosensitive contributors should review numerical traces and truth sidecars only.

Release build staging is cleaned before packaging. Debug calibration stimuli and raw controls are excluded from Release; inspect native package contents as well as JavaScript. Debug acquisition is for nonphotosensitive operators only.

A demonstration never shows unmitigated hazardous video at full speed. Use static numerical traces or warned stills/slideshows at ≤2 fps. Avoid animated flashing traces, fast cuts and full-screen blinking cards. The README GIF is a schematic with smooth ramps and constant background, containing no source-video frames. Actual bundled demo footage has no detected FAIL events; its illustrative Broadcast/Local cue must be labeled.

Closed-loop verification covers complete ramps at measured VVD offsets. It is a check of the detector and compositing model, not a medical guarantee, natural-film adjudication, or independent calibration of another player/display. Existing control-film flags and physical-device/cloud gaps remain visible in evaluation and submission documents.
