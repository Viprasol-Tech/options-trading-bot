"""Tests for the payoff-plot data exporter and the price grid helper."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from options_trading_bot.export import export_payoff, payoff_rows, to_csv, to_json
from options_trading_bot.payoff import price_grid
from options_trading_bot.strategies import bull_call_spread


def _strat() -> object:
    return bull_call_spread(95.0, 105.0, 7.0, 2.5)


def test_price_grid_endpoints_and_count() -> None:
    grid = price_grid(80.0, 120.0, 5)
    assert len(grid) == 5
    assert grid[0] == 80.0
    assert grid[-1] == 120.0
    assert math.isclose(grid[2], 100.0)


def test_price_grid_validation() -> None:
    with pytest.raises(ValueError):
        price_grid(120.0, 80.0, 5)
    with pytest.raises(ValueError):
        price_grid(80.0, 120.0, 1)


def test_payoff_rows_shape() -> None:
    rows = payoff_rows(_strat(), 80.0, 120.0, 11)  # type: ignore[arg-type]
    assert len(rows) == 11
    assert set(rows[0]) == {"spot", "payoff"}


def test_to_csv_has_header_and_rows() -> None:
    text = to_csv(_strat(), 80.0, 120.0, 5)  # type: ignore[arg-type]
    lines = text.strip().splitlines()
    assert lines[0] == "spot,payoff"
    assert len(lines) == 6  # header + 5 points


def test_to_json_has_metadata() -> None:
    doc = json.loads(to_json(_strat(), 80.0, 120.0, 5))  # type: ignore[arg-type]
    assert doc["strategy"] == "bull_call_spread"
    assert math.isclose(doc["net_premium"], -4.5)
    assert "break_evens" in doc
    assert len(doc["points"]) == 5


def test_export_csv_file(tmp_path: Path) -> None:
    out = tmp_path / "payoff.csv"
    written = export_payoff(_strat(), out, 80.0, 120.0, 9)  # type: ignore[arg-type]
    assert written.exists()
    assert written.read_text(encoding="utf-8").startswith("spot,payoff")


def test_export_json_file(tmp_path: Path) -> None:
    out = tmp_path / "payoff.json"
    export_payoff(_strat(), out, 80.0, 120.0, 9)  # type: ignore[arg-type]
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["strategy"] == "bull_call_spread"


def test_export_unknown_format_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        export_payoff(_strat(), tmp_path / "x.txt", 80.0, 120.0, 9)  # type: ignore[arg-type]
