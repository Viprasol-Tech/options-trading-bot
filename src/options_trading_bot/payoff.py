"""Option and strategy payoff diagrams at expiry.

Computes the payoff of single options and common multi-leg strategies across a
range of underlying prices — the standard way to visualise an options trade's
risk/reward before placing it.

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from options_trading_bot.bsm import OptionType


def option_payoff(spot: float, strike: float, option: OptionType, premium: float = 0.0) -> float:
    """Payoff of a single long option at expiry, net of premium paid."""
    intrinsic = max(0.0, spot - strike) if option is OptionType.CALL else max(0.0, strike - spot)
    return intrinsic - premium


def covered_call(spot: float, entry: float, strike: float, premium: float) -> float:
    """Payoff of long stock (bought at ``entry``) plus a short call at ``strike``."""
    stock = spot - entry
    short_call = premium - max(0.0, spot - strike)
    return stock + short_call


def long_straddle(spot: float, strike: float, call_premium: float, put_premium: float) -> float:
    """Payoff of a long straddle (long call + long put at the same strike)."""
    call = max(0.0, spot - strike) - call_premium
    put = max(0.0, strike - spot) - put_premium
    return call + put


def payoff_curve(spots: Sequence[float], fn: Callable[[float], float]) -> list[tuple[float, float]]:
    """Evaluate a single-arg payoff callable over a range of spot prices."""
    return [(s, fn(s)) for s in spots]
