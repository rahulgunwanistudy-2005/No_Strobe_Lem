# HTML5 reference overlay

Serve this folder over localhost/HTTPS and open `index.html` in Chrome/Firefox.
Enter a video URL and its verified `.hzt.json` or `.hzt.vtt` URL. CORS must permit
both downloads. The example hashes the source, binds it to `media.source_sha256`,
and unlocks its Play button only after verification checks. It downloads the
whole video to keep the example small; production hosts should bind a trusted
catalog/source checksum without buffering large movies in browser memory.

`reader.js` is a portable 60-line metadata-track reader. Import
`attachHazardTrack(video, overlay, trackUrl)` and cover the displayed video with
an absolutely positioned overlay. It refuses failing/unresolved tracks, pauses
on attach/disposal, and applies authoritative payload timing on every animation
frame. Pause, seek, ramps and overlap ties follow the spec. Cleanup restores an
opaque cover. Hosts must bind exact source bytes before permitting playback.
Do not add native controls before attachment succeeds.

No raw hazard media is bundled or autoplayed. For demonstrations use a slow
nonhazardous source or a trace/overlay-only view. Contract fixtures are fabricated
and must never be presented as analyzed media. Browser compositing/timing needs
its own calibration before making a measured mitigation claim.
