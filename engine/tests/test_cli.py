import json
from dataclasses import replace

from typer.testing import CliRunner

from nostrobe.cli import app
from nostrobe.synth.generator import ClipSpec, encode
from nostrobe.track import jsonio, webvtt


def test_cli_commands_and_error_mapping(tmp_path):
    runner = CliRunner()
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    for command in ("analyze", "verify", "report", "synth", "eval", "schema"):
        assert command in help_result.output
    result = runner.invoke(
        app, ["analyze", str(tmp_path / "missing.mp4"), "--out", str(tmp_path / "out")]
    )
    assert result.exit_code == 4
    assert runner.invoke(app, ["eval"]).exit_code == 6
    assert runner.invoke(app, ["synth", "--suite", "typo"]).exit_code == 1


def test_analyze_verify_report_default_profiles_and_binding(tmp_path, monkeypatch):
    monkeypatch.setenv("NOSTROBE_REPO_ROOT", str(tmp_path))
    video = tmp_path / "HAZARD_flat.mp4"
    encode(video, ClipSpec("flat", "flat", duration_s=0.2))
    output = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", str(video), "--out", str(output)])
    assert result.exit_code == 0, result.output
    for profile in ("broadcast", "local", "kids"):
        track = jsonio.parse((output / f"HAZARD_flat.{profile}.hzt.json").read_text())
        assert track.verifier.passes and not track.veils
        assert webvtt.parse((output / f"HAZARD_flat.{profile}.hzt.vtt").read_text()) == track
    trackpath = output / "HAZARD_flat.broadcast.hzt.json"
    result = runner.invoke(app, ["verify", str(video), str(trackpath)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["passes"]
    report = tmp_path / "traces.html"
    result = runner.invoke(
        app, ["report", str(trackpath), "--video", str(video), "--out", str(report)]
    )
    assert result.exit_code == 0, result.output
    assert "<video" not in report.read_text()
    original = video.read_bytes()
    assert (
        runner.invoke(
            app, ["report", str(trackpath), "--video", str(video), "--out", str(video)]
        ).exit_code
        == 1
    )
    assert video.read_bytes() == original
    payload = trackpath.read_text().replace(track.media.source_sha256, "0" * 64)
    trackpath.write_text(payload)
    assert runner.invoke(app, ["verify", str(video), str(trackpath)]).exit_code == 1


def test_unresolved_output_and_stale_artifact_removal(tmp_path, monkeypatch):
    from nostrobe import cli

    monkeypatch.setenv("NOSTROBE_REPO_ROOT", str(tmp_path))
    original = cli.get_profile
    monkeypatch.setattr(cli, "get_profile", lambda p: replace(original(p), max_alpha=0.02))
    video = tmp_path / "HAZARD_flash.mp4"
    encode(video, ClipSpec("flash", "full_flash", duration_s=2))
    output = tmp_path / "out"
    output.mkdir()
    stale = output / "HAZARD_flash.broadcast.hzt.json"
    stale.write_text("stale")
    (output / "HAZARD_flash.broadcast.hzt.vtt").write_text("stale")
    runner = CliRunner()
    result = runner.invoke(
        app, ["analyze", str(video), "--profile", "broadcast", "--out", str(output)]
    )
    assert result.exit_code == 2, result.output
    assert not stale.exists() and not (output / "HAZARD_flash.broadcast.hzt.vtt").exists()
    track = jsonio.parse(
        (output / "HAZARD_flash.broadcast.unresolved.hzt.json").read_text(), allow_unresolved=True
    )
    assert not track.verifier.passes and track.unresolved_segments
    assert not list(output.glob("*.hzt.vtt"))
