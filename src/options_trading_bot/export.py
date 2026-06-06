"""Payoff-plot data exporter.

Turns a strategy's expiry payoff curve into plot-ready data you can feed straight
into matplotlib, Excel, or a web charting library — without this package taking a
hard dependency on any of them. Supports CSV and JSON, to a file or a string.

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from options_trading_bot.strategies import Strategy

__all__ = ["export_payoff", "payoff_rows", "to_csv", "to_json"]


def payoff_rows(
    strategy: Strategy, low: float, high: float, steps: int = 41
) -> list[dict[str, float]]:
    """Sample the strategy payoff into a list of ``{"spot", "payoff"}`` rows."""
    return [
        {"spot": round(s, 6), "payoff": round(p, 6)}
        for s, p in strategy.payoff_curve(low, high, steps)
    ]


def to_csv(strategy: Strategy, low: float, high: float, steps: int = 41) -> str:
    """Render the payoff curve as a CSV string with a ``spot,payoff`` header."""
    rows = payoff_rows(strategy, low, high, steps)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["spot", "payoff"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def to_json(strategy: Strategy, low: float, high: float, steps: int = 41) -> str:
    """Render a JSON document with strategy metadata and the payoff series."""
    rows = payoff_rows(strategy, low, high, steps)
    doc = {
        "strategy": strategy.name,
        "net_premium": round(strategy.net_premium(), 6),
        "break_evens": [round(b, 6) for b in strategy.break_evens(low, high)],
        "max_profit": round(strategy.max_profit(low, high), 6),
        "max_loss": round(strategy.max_loss(low, high), 6),
        "points": rows,
    }
    return json.dumps(doc, indent=2)


def export_payoff(
    strategy: Strategy,
    path: str | Path,
    low: float,
    high: float,
    steps: int = 41,
    fmt: str | None = None,
) -> Path:
    """Write the payoff curve to ``path`` as CSV or JSON.

    Args:
        strategy: The strategy to export.
        path: Destination file path. The extension picks the format unless ``fmt``
            is given.
        low: Lowest underlying price in the grid.
        high: Highest underlying price in the grid.
        steps: Number of grid points.
        fmt: Force ``"csv"`` or ``"json"``; otherwise inferred from the extension.

    Returns:
        The :class:`~pathlib.Path` written.
    """
    p = Path(path)
    chosen = (fmt or p.suffix.lstrip(".")).lower()
    if chosen == "csv":
        text = to_csv(strategy, low, high, steps)
    elif chosen == "json":
        text = to_json(strategy, low, high, steps)
    else:
        raise ValueError(f"unsupported export format: {chosen!r} (use 'csv' or 'json')")
    p.write_text(text, encoding="utf-8")
    return p
