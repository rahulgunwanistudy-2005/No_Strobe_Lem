# Playback fixtures

`raw/demo.mp4` is the first twelve seconds of Big Buck Bunny (2008),
Blender Foundation / Peach team, CC-BY-3.0.
License: https://peach.blender.org/about/ . Extracted/scaled from the
checksum-pinned original in engine/eval/manifest.yaml.
`demo.json` carries the source checksum and license. `catalog.json` binds the
poster, packaged video and three matching profile sidecars. All sidecars were
verified at the measured S5 offsets −0.268875/0/+0.268875 s. The source has no
FAIL events. Broadcast/Local retain a gentle illustrative cue with no covered
hazard ids. Kids covers both source warnings with a whole-excerpt illustrative
veil (alpha 0.10, gray 0.25), checked with warning rejection at every offset.
This recipe is not a new production solver or minimum-distortion result.
`demo.hzt.json` is the legacy Broadcast alias. Reproduce with
`tools/prepare_demo.py`; the original film checksum is pinned.

The sync/compositing files in `../calibration-assets/` are deterministic nonhazardous device stimuli from
`tools/generate_calibration.py`. All three profiles returned zero fail/warn
on their encoded source. Instant calibration descriptors are loaded only in
debug builds. The build wrapper includes their MP4 files only in Debug; they
cannot pass the production HazardTrack reader. Calibration clips stay paused
until explicitly started. Verified catalog selection autoplays the demo only
after surface, metadata and veil readiness. Calibration stimuli are not
recorded measurements.
