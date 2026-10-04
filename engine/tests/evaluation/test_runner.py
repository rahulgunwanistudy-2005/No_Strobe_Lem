import json

from typer.testing import CliRunner

from nostrobe.cli import app
from nostrobe.evaluation import runner
from nostrobe.evaluation.manifest import Source, fetch, read_manifest
from nostrobe.evaluation.suites import shape_specs


def tiny_manifest(tmp_path):
    path = tmp_path / "manifest.yaml"
    path.write_text(
        json.dumps(
            dict(
                version="1.0", seed=7, fps=[25], shapes_count=1, sources=[], realistic=[], clean=[]
            )
        )
    )
    return path


def test_bad_checksum_is_rejected_before_use(tmp_path):
    path = tmp_path / "film.mov"
    path.write_bytes(b"changed")
    source = Source(
        id="film",
        title="film",
        author="author",
        license="CC-BY-3.0",
        license_url="https://example.org/license",
        url="https://example.org/film.mov",
        sha256="0" * 64,
    )
    import pytest

    with pytest.raises(ValueError, match="checksum"):
        fetch(source, tmp_path)


def test_two_eval_runs_produce_byte_identical_artifacts(tmp_path, monkeypatch):
    manifest = tiny_manifest(tmp_path)
    monkeypatch.setenv("NOSTROBE_REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(
        runner,
        "environment",
        lambda _: {"ffmpeg": "fixture", "python": "3.12", "machine": "fixture", "params_hash": {}},
    )
    monkeypatch.setattr(runner, "code_hash", lambda _: "0" * 64)
    monkeypatch.setattr(runner, "boundary_specs", lambda *_: [])
    monkeypatch.setattr(runner, "shape_specs", lambda *_: [shape_specs(7, 1, [25])[0]])
    out = tmp_path / "out"
    cli = CliRunner()
    args = ["eval", "--manifest", str(manifest), "--out", str(out)]
    first = cli.invoke(app, args)
    assert first.exit_code == 0, first.output
    original = (out / "results.json").read_bytes(), (out / "RESULTS.md").read_bytes()
    second = cli.invoke(app, args)
    assert second.exit_code == 0, second.output
    assert original == ((out / "results.json").read_bytes(), (out / "RESULTS.md").read_bytes())
    result = json.loads(original[0])
    assert result["gates_pass"]
    assert len(result["observations"]) == 3
    assert "<video" not in (out / "RESULTS.md").read_text()


def test_unknown_source_manifest_is_rejected(tmp_path):
    import pytest

    path = tiny_manifest(tmp_path)
    payload = json.loads(path.read_text())
    payload["clean"] = ["missing"]
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="unknown footage"):
        read_manifest(path)


def test_reused_evidence_rejects_changed_generated_media(tmp_path, monkeypatch):
    manifest = tiny_manifest(tmp_path)
    monkeypatch.setenv("NOSTROBE_REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(
        runner,
        "environment",
        lambda _: {"ffmpeg": "fixture", "python": "3.12", "machine": "fixture", "params_hash": {}},
    )
    monkeypatch.setattr(runner, "code_hash", lambda _: "0" * 64)
    monkeypatch.setattr(runner, "boundary_specs", lambda *_: [])
    cli = CliRunner()
    args = ["eval", "--manifest", str(manifest), "--out", str(tmp_path / "out")]
    assert cli.invoke(app, args).exit_code == 0
    path = next((tmp_path / "synth_out/s4/clips").glob("*.mp4"))
    path.write_bytes(b"changed bytes")
    result = cli.invoke(app, [*args, "--resume"])
    assert result.exit_code == 1
    assert "checksum" in str(result.exception) or "source mismatch" in result.output
