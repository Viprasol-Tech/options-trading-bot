"""CLI for Options Trading Bot.

Subcommands:

- ``price``         Black-Scholes price + Greeks for a single option.
- ``iv``            Solve implied volatility from a market price (Newton + bisection).
- ``covered-call``  Quick covered-call payoff at a few spots.
- ``strategy``      Build a multi-leg strategy and show payoff/break-evens/Greeks.
- ``export``        Write a strategy payoff curve to CSV or JSON for plotting.

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from options_trading_bot import __version__
from options_trading_bot.bsm import Greeks, OptionType, greeks, price
from options_trading_bot.export import export_payoff
from options_trading_bot.iv import IVError, implied_volatility
from options_trading_bot.payoff import covered_call
from options_trading_bot.strategies import (
    Strategy,
    bear_call_spread,
    bear_put_spread,
    bull_call_spread,
    bull_put_spread,
    iron_condor,
    long_call_butterfly,
    long_strangle,
)

app = typer.Typer(add_completion=False, help="Options Trading Bot - by Viprasol Tech.")
console = Console()


def _greeks_table(g: Greeks) -> Table:
    table = Table(show_header=True)
    for name in ("delta", "gamma", "vega", "theta", "rho"):
        table.add_column(name)
    table.add_row(
        f"{g.delta:.4f}",
        f"{g.gamma:.5f}",
        f"{g.vega:.4f}",
        f"{g.theta:.4f}",
        f"{g.rho:.4f}",
    )
    return table


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"options-trading-bot [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command(name="price")
def price_cmd(
    spot: float = 100.0,
    strike: float = 100.0,
    days: float = 30.0,
    rate: float = 0.05,
    vol: float = 0.20,
    put: bool = typer.Option(False, "--put", help="Price a put instead of a call."),
) -> None:
    """Price a European option (Black-Scholes) and show its Greeks."""
    opt = OptionType.PUT if put else OptionType.CALL
    t = days / 365.0
    p = price(spot, strike, t, rate, vol, opt)
    g = greeks(spot, strike, t, rate, vol, opt)
    console.print(f"{opt.value.title()}  S={spot} K={strike} T={days}d r={rate} vol={vol}")
    console.print(f"Price: [bold green]{p:.4f}[/]")
    console.print(_greeks_table(g))


@app.command(name="iv")
def iv_cmd(
    market_price: float = typer.Argument(..., help="Observed market option price."),
    spot: float = 100.0,
    strike: float = 100.0,
    days: float = 30.0,
    rate: float = 0.05,
    put: bool = typer.Option(False, "--put", help="Treat the price as a put."),
) -> None:
    """Solve the implied volatility that reproduces a market price."""
    opt = OptionType.PUT if put else OptionType.CALL
    t = days / 365.0
    try:
        vol = implied_volatility(market_price, spot, strike, t, rate, opt)
    except IVError as exc:
        console.print(f"[bold red]Could not solve IV:[/] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(
        f"{opt.value.title()}  price={market_price} S={spot} K={strike} T={days}d r={rate}"
    )
    console.print(f"Implied volatility: [bold green]{vol:.4%}[/]")


@app.command(name="covered-call")
def covered_call_cmd(entry: float = 100.0, strike: float = 110.0, premium: float = 3.0) -> None:
    """Show a covered-call payoff at several underlying prices."""
    console.print(f"Covered call: long stock @ {entry}, short {strike} call for {premium}")
    for spot in (90.0, 100.0, 110.0, 120.0):
        pnl = covered_call(spot, entry, strike, premium)
        color = "green" if pnl >= 0 else "red"
        console.print(f"  spot {spot:>6.1f} -> P/L [bold {color}]{pnl:+.2f}[/]")


# --- strategy builders, keyed by name for the `strategy`/`export` commands -----


def _build_strategy(name: str) -> Strategy:
    """Construct a demo instance of a named strategy with sensible default strikes."""
    builders = {
        "bull-call": lambda: bull_call_spread(95.0, 105.0, 7.0, 2.5),
        "bear-put": lambda: bear_put_spread(95.0, 105.0, 2.5, 7.0),
        "bull-put": lambda: bull_put_spread(95.0, 105.0, 2.5, 7.0),
        "bear-call": lambda: bear_call_spread(95.0, 105.0, 7.0, 2.5),
        "iron-condor": lambda: iron_condor(90.0, 95.0, 105.0, 110.0, (1.0, 2.5, 2.5, 1.0)),
        "butterfly": lambda: long_call_butterfly(95.0, 100.0, 105.0, (7.0, 3.5, 1.2)),
        "strangle": lambda: long_strangle(95.0, 105.0, 2.0, 2.0),
    }
    if name not in builders:
        available = ", ".join(sorted(builders))
        raise typer.BadParameter(f"unknown strategy {name!r}; choose from: {available}")
    return builders[name]()


@app.command(name="strategy")
def strategy_cmd(
    name: str = typer.Argument(
        ...,
        help="bull-call | bear-put | bull-put | bear-call | iron-condor | butterfly | strangle",
    ),
    low: float = 80.0,
    high: float = 120.0,
    spot: float = 100.0,
    days: float = 30.0,
    rate: float = 0.05,
    vol: float = 0.20,
) -> None:
    """Build a multi-leg strategy and report payoff, break-evens, and Greeks."""
    strat = _build_strategy(name)
    net = strat.net_premium()
    flow = "credit" if net >= 0 else "debit"
    console.print(f"[bold]{strat.name}[/]  net {flow} = [bold]{abs(net):.2f}[/]")

    table = Table(show_header=True, title="Payoff at expiry")
    table.add_column("spot", justify="right")
    table.add_column("P/L", justify="right")
    for s, pl in strat.payoff_curve(low, high, steps=9):
        color = "green" if pl >= 0 else "red"
        table.add_row(f"{s:.1f}", f"[{color}]{pl:+.2f}[/]")
    console.print(table)

    bes = ", ".join(f"{b:.2f}" for b in strat.break_evens(low, high)) or "none"
    console.print(f"Break-even(s): [cyan]{bes}[/]")
    console.print(
        f"Max profit: [green]{strat.max_profit(low, high):+.2f}[/]   "
        f"Max loss: [red]{strat.max_loss(low, high):+.2f}[/]"
    )
    t = days / 365.0
    console.print("Position Greeks:")
    console.print(_greeks_table(strat.position_greeks(spot, t, rate, vol)))


@app.command(name="export")
def export_cmd(
    name: str = typer.Argument(..., help="Strategy name (see `strategy --help`)."),
    out: Path = typer.Option("payoff.csv", "--out", "-o", help="Output .csv or .json path."),
    low: float = 80.0,
    high: float = 120.0,
    steps: int = 41,
) -> None:
    """Export a strategy payoff curve to CSV or JSON for plotting."""
    strat = _build_strategy(name)
    written = export_payoff(strat, out, low, high, steps)
    console.print(
        f"Wrote {steps} payoff points for [bold]{strat.name}[/] to "
        f"[green]{written}[/] ({written.suffix.lstrip('.') or 'csv'})"
    )


if __name__ == "__main__":
    app()
