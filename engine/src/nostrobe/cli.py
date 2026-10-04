"""Thin command entry points with strict verified-track publication gates."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from nostrobe.analysis import analyze as analyze_video
from nostrobe.config import Settings
from nostrobe.decode.cache import FrameCache, load_cache
from nostrobe.detect.pipeline import analyze_detect_all
from nostrobe.domain.models import HazardTrack
from nostrobe.domain.profiles import get_profile
from nostrobe.domain.schema import write_schema
from nostrobe.errors import (
    DecodeError,
    NostrobeError,
    ProfileError,
    UnsupportedMediaError,
    VerifierFailedError,
)
from nostrobe.logging import configure_logging
from nostrobe.report.html import render
from nostrobe.synth.generator import generate_suite
from nostrobe.track import jsonio, webvtt
from nostrobe.verify.verifier import verify as verify_track

app = typer.Typer(no_args_is_help=True, help="No Strobe-lem offline tools")


@app.callback()
def main() -> None:
    configure_logging(Settings().log_level)


def _run(action: Callable[[], None]) -> None:
    try:
        action()
    except (NostrobeError, OSError, ValueError, NotImplementedError) as exc:
        codes: dict[type[Exception], int] = {
            DecodeError: 4,
            UnsupportedMediaError: 3,
            VerifierFailedError: 2,
            ProfileError: 5,
            NotImplementedError: 6,
        }
        message = " ".join(str(exc).split())
        logging.getLogger("nostrobe").error(message)
        raise typer.Exit(codes.get(type(exc), 1)) from exc


@app.command()
def analyze(
    path: Path,
    detect_only: Annotated[bool, typer.Option()] = False,
    profile: Annotated[str, typer.Option()] = "all",
    output: Annotated[Path | None, typer.Option()] = None,
    out: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Analyze all profiles, verify veils, and write tracks plus a static report."""

    def action() -> None:
        params = None if profile == "all" else [get_profile(profile)]
        if not detect_only:
            if output is not None and out is not None:
                raise ValueError("choose --out or --output, not both")
            tracks = analyze_video(path, out or output or Path("analysis_out"), params)
            if any(not track.verifier.passes for track in tracks):
                raise VerifierFailedError(
                    "unresolved segments; only debug JSON written for failing profiles"
                )
            return
        if out is not None:
            raise ValueError("detection-only output uses --output")
        if output is not None:
            if output.name.lower().endswith((".hzt.json", ".hzt.vtt")):
                raise ValueError("detection output cannot use a HazardTrack extension")
            if output.resolve() == path.resolve():
                raise ValueError("detection output cannot overwrite the input video")
        events = analyze_detect_all(path, profiles=params)
        payload = {
            "format": "nostrobe-detection",
            "format_version": "1.0",
            "verified": False,
            "profiles": {
                key: {
                    "params_hash": get_profile(key).params_hash(),
                    "events": [event.model_dump(mode="json") for event in values],
                }
                for key, values in events.items()
            },
        }
        serialized = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if output is None:
            typer.echo(serialized, nl=False)
        else:
            output.write_text(serialized)

    _run(action)


def _read_track(path: Path, *, debug: bool = False) -> HazardTrack:
    return (
        webvtt.parse(path.read_text())
        if path.suffix == ".vtt"
        else jsonio.parse(path.read_text(), allow_unresolved=debug)
    )


def _matching_cache(video: Path, track: HazardTrack) -> FrameCache:
    cache = load_cache(video)
    if cache.media.source_sha256 != track.media.source_sha256:
        raise ValueError("video SHA-256 does not match the track")
    if get_profile(track.profile).params_hash() != track.verifier.params_hash:
        raise ValueError("track parameters do not match this engine")
    return cache


@app.command()
def verify(path: Path, track: Path) -> None:
    """Re-verify an existing JSON or WebVTT track against the matching video."""

    def action() -> None:
        artifact = _read_track(track, debug=True)
        cache = _matching_cache(path, artifact)
        result = verify_track(cache, artifact.veils, artifact.profile)
        typer.echo(result.model_dump_json())
        if not result.passes or artifact.unresolved_segments:
            raise VerifierFailedError("track remains unresolved")

    _run(action)


@app.command()
def report(
    path: Path,
    output: Annotated[Path, typer.Option("--out", "--output")] = Path("report.html"),
    video: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Render a static report, with source traces when --video is supplied."""

    def action() -> None:
        track = _read_track(path, debug=True)
        if output.resolve() == path.resolve() or (
            video is not None and output.resolve() == video.resolve()
        ):
            raise ValueError("report cannot overwrite an input")
        cache = None if video is None else _matching_cache(video, track)
        output.write_text(render(track, cache=cache))

    _run(action)


@app.command(name="eval")
def evaluate(
    manifest: Annotated[Path | None, typer.Option()] = None,
    output: Annotated[Path | None, typer.Option("--out", "--output")] = None,
    suite: Annotated[str, typer.Option()] = "all",
    fresh_measurements: Annotated[bool, typer.Option()] = False,
    resume: Annotated[bool, typer.Option()] = False,
) -> None:
    """Regenerate measured evaluation results, retaining honest gate failures."""
    from nostrobe.evaluation.runner import run_eval

    def action() -> None:
        passed = run_eval(
            manifest_path=manifest,
            output=output,
            suite=suite,
            fresh_measurements=fresh_measurements,
            resume=resume,
        )
        if not passed:
            raise VerifierFailedError(
                "evaluation incomplete or acceptance gate failed; see RESULTS.md"
            )

    _run(action)


@app.command()
def synth(
    suite: str = "smoke", seed: int = 7, output: Annotated[Path | None, typer.Option()] = None
) -> None:
    """Generate warning-labeled synthetic clips without playing them."""

    def action() -> None:
        config = Settings()
        paths = generate_suite(output or config.synth_dir, suite, seed, settings=config)
        logging.getLogger("nostrobe").info("generated %d clips with truth sidecars", len(paths))

    _run(action)


@app.command()
def schema(output: Annotated[Path | None, typer.Option()] = None) -> None:
    """Write canonical HazardTrack JSON Schema."""
    _run(lambda: write_schema(output or Settings().schema_path))


if __name__ == "__main__":
    app()
