# HazardTrack

Apache-2.0 reference library and open, timed video-mitigation format. The Python
package and CLI are named `nostrobe`. Analyze an SDR video once; distribute a
verified `.hzt.json` / `.hzt.vtt` beside it; apply a timed uniform veil during
playback. Detection, mitigation and verification are deterministic.

No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.

## Install and analyze

Python 3.12 and ffmpeg/ffprobe >=6 are required. Source video must have explicit
limited-range, 8-bit SDR BT.709 metadata. HDR and unspecified transfer are refused.

```sh
uv sync --project engine --locked
uv run --project engine nostrobe analyze input.mp4 --out analysis_out
uv run --project engine nostrobe verify input.mp4 analysis_out/input.broadcast.hzt.json
```

The analyzer processes Broadcast, Local and Kids. It writes verified sidecars and
a static trace report. Failing profiles produce debug JSON only, never a playable
track. The verifier includes ramps and checks measured VVD offsets of
−268.875/0/+268.875 ms. These measurements apply to that device setup; other
players need independent synchronization and compositing calibration.

- [Format and playback semantics](spec/HAZARDTRACK.md)
- [JSON Schema](schema/hazardtrack.schema.json)
- [HTML5 metadata reader and safe demo](examples/web/README.md)
- [Contributing](CONTRIBUTING.md)
- [Standards interpretations](docs/INTERPRETATIONS.md)
- [Evaluation evidence](engine/eval/RESULTS.md)

Historical evaluation/device evidence is preserved with its original provenance;
this repository's CI independently tests the extracted library. No AWS handler,
TV application or device acquisition tooling is included. Contract fixtures are
fabricated examples, not evidence of analyzed media. The Python source is
extracted from No Strobe-lem; the product pins this repository's release.
