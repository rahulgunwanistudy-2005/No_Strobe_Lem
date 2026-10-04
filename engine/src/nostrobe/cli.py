"""Thin command entry points. Unimplemented stages refuse to produce tracks."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from nostrobe.config import Settings
from nostrobe.detect.pipeline import analyze_detect_all
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
from nostrobe.synth.generator import generate_suite

app = typer.Typer(no_args_is_help=True, help="No Strobe-lem offline tools")


@app.callback()
def main() -> None:
    configure_logging(Settings().log_level)


def _run(action: Callable[[], None]) -> None:
    try:
        action()
    except (NostrobeError, OSError, ValueError, NotImplementedError) as exc:
        codes: dict[type[Exception], int] = {
            DecodeError: 2,
            UnsupportedMediaError: 3,
            VerifierFailedError: 4,
            ProfileError: 5,
            NotImplementedError: 6,
        }
        message = " ".join(str(exc).split())
        logging.getLogger("nostrobe").error(message)
        raise typer.Exit(codes.get(type(exc), 1)) from exc


def _deferred(stage: str) -> None:
    raise NotImplementedError(f"{stage} is not implemented in Session 1")


@app.command()
def analyze(
    path: Path,
    detect_only: Annotated[bool, typer.Option()] = False,
    profile: Annotated[str, typer.Option()] = "all",
    output: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Emit unverified detection events; track publishing requires S3."""

    def action() -> None:
        if not detect_only:
            _deferred("verified analyze")
        params = None if profile == "all" else [get_profile(profile)]
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
            if output.name.endswith((".hzt.json", ".hzt.vtt")):
                raise ValueError("detection output cannot use a HazardTrack extension")
            output.write_text(serialized)

    _run(action)


@app.command()
def verify(path: Path) -> None:
    """Verify a mitigated track (S3)."""
    _run(lambda: _deferred("verify"))


@app.command()
def report(path: Path) -> None:
    """Render an analysis report (S3)."""
    _run(lambda: _deferred("report"))


@app.command(name="eval")
def evaluate() -> None:
    """Run the evaluation harness (S4)."""
    _run(lambda: _deferred("eval"))


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
