from typer.testing import CliRunner

from nostrobe.cli import app


def test_cli_lists_commands_and_refuses_deferred_work() -> None:
    runner = CliRunner()
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    for command in ("analyze", "verify", "report", "synth", "eval", "schema"):
        assert command in help_result.output
    for command in ("analyze", "verify", "report"):
        result = runner.invoke(app, [command, "example.mp4"])
        assert result.exit_code == 6
        assert "not implemented" in result.output
    assert runner.invoke(app, ["eval"]).exit_code == 6
    assert runner.invoke(app, ["synth", "--suite", "typo"]).exit_code == 1
