"""End-to-end example for Options Trading Bot.

Run from the repo root::

    PYTHONPATH=src python examples/quickstart.py

Shows pricing + Greeks, recovering implied volatility from a market price, and
analysing an iron condor (payoff, break-evens, risk, position Greeks) plus a
CSV export of its payoff curve for plotting.
"""

from __future__ import annotations

from pathlib import Path

from options_trading_bot import (
    OptionType,
    greeks,
    implied_volatility,
    iron_condor,
    price,
)
from options_trading_bot.export import export_payoff


def main() -> None:
    spot, strike, t, r, vol = 100.0, 105.0, 30 / 365, 0.05, 0.25

    # 1) Price a call and inspect its Greeks.
    call = price(spot, strike, t, r, vol, OptionType.CALL)
    g = greeks(spot, strike, t, r, vol, OptionType.CALL)
    print(f"Call price: {call:.4f}")
    print(f"Delta {g.delta:.4f}  Gamma {g.gamma:.5f}  Vega {g.vega:.4f}")

    # 2) Recover implied volatility from that price (round-trips to ~0.25).
    iv = implied_volatility(call, spot, strike, t, r, OptionType.CALL)
    print(f"Implied vol from price {call:.4f}: {iv:.4%}")

    # 3) Build an iron condor and analyse it.
    condor = iron_condor(90.0, 95.0, 105.0, 110.0, premiums=(1.0, 2.5, 2.5, 1.0))
    print(f"\n{condor.name}: net credit {condor.net_premium():+.2f}")
    print(f"Break-evens: {[round(b, 2) for b in condor.break_evens(70.0, 130.0)]}")
    print(
        f"Max profit {condor.max_profit(70.0, 130.0):+.2f}  "
        f"Max loss {condor.max_loss(70.0, 130.0):+.2f}"
    )

    # 4) Export the payoff curve for plotting.
    out = Path("condor_payoff.csv")
    export_payoff(condor, out, low=80.0, high=120.0, steps=41)
    print(f"\nWrote payoff curve -> {out}")


if __name__ == "__main__":
    main()
