# HTML5 reference overlay

Import `attachHazardTrack(video, overlay, jsonUrl)` from `reader.js`. Position
`overlay` absolutely above the video, covering its complete displayed area,
with `pointer-events:none`. Call the returned cleanup function on disposal.
The reader refuses unresolved tracks and never starts playback. Hosts must bind
the track to its exact video, handle download errors before enabling playback,
and implement their own catalog/controls. No raw demo media is bundled.
