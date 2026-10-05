# Playback fixtures

`raw/demo.mp4` is the first twelve seconds of Big Buck Bunny (2008),
Blender Foundation / Peach team, CC-BY-3.0.
License: https://peach.blender.org/about/ . Extracted/scaled from the
checksum-pinned original in engine/eval/manifest.yaml.
`demo.json` carries the source checksum and license. `demo.hzt.json` was
actually verified at the current simulated offsets; the gentle illustrative
veil does not represent a hazard in this excerpt.

The sync/compositing files in `../calibration-assets/` are deterministic nonhazardous device stimuli from
`tools/generate_calibration.py`. All three profiles returned zero fail/warn
on their encoded source. Instant calibration descriptors are loaded only in
debug builds. The build wrapper includes their MP4 files only in Debug; they cannot pass the production HazardTrack reader. None of these
clips autoplay. They are stimuli, not recorded measurements.
