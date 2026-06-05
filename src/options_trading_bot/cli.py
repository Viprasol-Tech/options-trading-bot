"""CLI for Options Trading Bot.

``options-trading-bot price`` prices an option and prints its Greeks;
``options-trading-bot covered-call`` shows a covered-call payoff at a few spots.

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from options_trading_bot import __version__
from options_trading_bot.bsm import OptionType, greeks, price
from options_trading_bot.payoff import covered_call

app = typer.Typer(add_completion=False, help="Options Trading Bot — by Viprasol Tech.")
console = Console()


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"options-trading-bot [bold cyan]{__version__}[/] — by Viprasol Tech")


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
    table = Table(show_header=True)
    for name in ("delta", "gamma", "vega", "theta", "rho"):
        table.add_column(name)
    table.add_row(
        f"{g.delta:.4f}", f"{g.gamma:.5f}", f"{g.vega:.4f}", f"{g.theta:.4f}", f"{g.rho:.4f}"
    )
    console.print(table)


@app.command(name="covered-call")
def covered_call_cmd(entry: float = 100.0, strike: float = 110.0, premium: float = 3.0) -> None:
    """Show a covered-call payoff at several underlying prices."""
    console.print(f"Covered call: long stock @ {entry}, short {strike} call for {premium}")
    for spot in (90.0, 100.0, 110.0, 120.0):
        pnl = covered_call(spot, entry, strike, premium)
        color = "green" if pnl >= 0 else "red"
        console.print(f"  spot {spot:>6.1f} -> P/L [bold {color}]{pnl:+.2f}[/]")


if __name__ == "__main__":
    app()
