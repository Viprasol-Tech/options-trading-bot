"""Smoke tests for the CLI subcommands via Typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from options_trading_bot import __version__
from options_trading_bot.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_price_command() -> None:
    result = runner.invoke(app, ["price", "--spot", "100", "--strike", "100"])
    assert result.exit_code == 0
    assert "Price:" in result.stdout
    assert "delta" in result.stdout


def test_iv_command_round_trip() -> None:
    # Price an ATM call (~2.3 at these inputs) then ask the CLI to recover IV.
    result = runner.invoke(
        app,
        ["iv", "2.3", "--spot", "100", "--strike", "100", "--days", "30", "--rate", "0.05"],
    )
    assert result.exit_code == 0
    assert "Implied volatility:" in result.stdout


def test_iv_command_bad_price_exits_nonzero() -> None:
    # Price above the achievable maximum -> solver error -> exit code 1.
    result = runner.invoke(app, ["iv", "9999", "--spot", "100", "--strike", "100"])
    assert result.exit_code == 1


def test_strategy_command() -> None:
    result = runner.invoke(app, ["strategy", "iron-condor"])
    assert result.exit_code == 0
    assert "iron_condor" in result.stdout
    assert "Break-even" in result.stdout


def test_strategy_unknown_name() -> None:
    result = runner.invoke(app, ["strategy", "not-a-strategy"])
    assert result.exit_code != 0


def test_export_command_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "bcs.csv"
    result = runner.invoke(app, ["export", "bull-call", "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("spot,payoff")


def test_covered_call_command() -> None:
    result = runner.invoke(app, ["covered-call"])
    assert result.exit_code == 0
    assert "Covered call" in result.stdout
