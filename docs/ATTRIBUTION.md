# Attribution

SDR luminance reference: ITU-R BT.1702-3 (11/2023), Annex 2 Table 1.
Source PDF URLs and edition references are in INTERPRETATIONS.md and the CSV header.
No reference footage or external application code is included in Session 1.
Vega stock hello-world is used only for local environment validation, outside this repository.

## S2 benchmark footage

Big Buck Bunny (2008), © Blender Foundation / www.bigbuckbunny.org,
licensed under [Creative Commons Attribution 3.0](https://peach.blender.org/about/).
[Official download page](https://peach.blender.org/download/);
[1080p H.264 source archive](https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_1080p_h264.mov.zip).

The unmodified `big_buck_bunny_1080p_h264.mov` is 1920×1080, 24 fps,
596.458333 seconds (approximately ten minutes). SHA-256:
`dc2146a2b1172def56730143ad80cd1825b7fad15f1fc9c23a4e7d01a741ac11`.
It was downloaded to a temporary directory and analyzed without playback.
Only numerical benchmark measurements are committed. Flagged intervals remain
unreviewed; this film is not asserted to be a verified clean control.

## S4 evaluation footage

Official license pages were retrieved on 2026-10-05 and archived in
`engine/eval/sources/` before using the films. Both explicitly license their
project results under [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/).
Excluded logos and trademarks are not claimed as licensed project assets.

- **Big Buck Bunny (2008)** — © Blender Foundation / Peach team,
  www.bigbuckbunny.org. [Official license](https://peach.blender.org/about/).
  The pinned 1080p H.264 MOV is retained unmodified for the full-film control.
- **Tears of Steel (2012)** — (CC) Blender Foundation / Mango team,
  mango.blender.org. [Official license](https://mango.blender.org/sharing/).
  [Official 720p MOV](https://download.blender.org/demo/movies/ToS/tears_of_steel_720p.mov).

`engine/eval/manifest.yaml` pins download and extracted-file SHA-256 checksums.
`uv run python eval/download_sources.py` fetches once and verifies every reuse.
The realistic suite extracts three-second moving excerpts and alpha-composites
camera-flash, repeated lightning, police-light, strobe and glitch effects in
RGB display-code space (90% effect, 10% original). These are modified test
assets, named `HAZARD_`, held only in ignored `synth_out/`; no autoplay.
Scenario names describe intended effects, not independently annotated scene
semantics. Original films remain byte-identical and contain unreviewed flags.

## Bundled demonstration and S8 assets

The native app bundles the credited 12-second opening excerpt of Big Buck Bunny
under CC-BY-3.0: resized to 640×360, audio removed, with a poster derived from
the same footage. The app's catalog and Attribution view retain credit, license,
source link and modifications. [TV asset inventory](../tv/assets/README.md)
records the encoded source hash and the illustrative Broadcast/Local overlays;
Kids covers measured warning events. No raw calibration or `HAZARD_` stimulus
is included in the Release package.

The 20-second S8 timeline GIF and static preview are original schematic artwork
produced by [the renderer](../tools/render_submission_preview.py), using
Pillow and matplotlib's DejaVu Sans font. They display a timeline, smooth gray
overlay and cursor; they contain no source film frames or flashing stimulus.
The GIF is released with this repository under Apache-2.0. It illustrates
playback semantics and is not a detector result or timing measurement.
