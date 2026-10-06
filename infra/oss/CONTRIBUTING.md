# Contributing

Open an issue with a reproducible input description or submit a pull request.
Use luminance traces and static frames to discuss hazardous content. Do not
attach autoplaying strobe clips; photosensitive contributors must never need to
review raw video. Synthetic outputs use HAZARD_ names and warning files.

Install Python 3.12, uv and ffmpeg >=6, then run:

```sh
cd engine
uv sync --locked
uv run ruff check
uv run ruff format --check
uv run mypy --strict src
uv run pytest -q
```

Tests include the generated schema and shared 500-sample playback fixture.
Changes to detector rules require primary-source citations and unchanged
independent ground truth. Never relax a gate to fit the implementation.
Regenerate schema with `uv run nostrobe schema`; mirror it into `../schema/`.
Keep `examples/web/` identical to `spec/examples/web/`. CI checks both copies.

Code contributions are under Apache-2.0. Retain attribution and source licenses.
