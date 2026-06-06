"""Option and strategy payoff diagrams at expiry.

Computes the payoff of single options and common multi-leg strategies across a
range of underlying prices — the standard way to visualise an options trade's
risk/reward before placing it. The :class:`OptionLeg` primitive lets you compose
arbitrary multi-leg strategies (see :mod:`options_trading_bot.strategies`).

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

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


@dataclass(slots=True, frozen=True)
class OptionLeg:
    """A single option leg of a strategy.

    Attributes:
        option: CALL or PUT.
        strike: Strike price.
        quantity: Signed contract count — positive is long, negative is short.
        premium: Per-contract premium paid (long) or received (short, still
            entered as a positive number; the sign of ``quantity`` handles cash flow).
    """

    option: OptionType
    strike: float
    quantity: float = 1.0
    premium: float = 0.0

    def intrinsic(self, spot: float) -> float:
        """Per-contract intrinsic value at ``spot`` (always >= 0)."""
        if self.option is OptionType.CALL:
            return max(0.0, spot - self.strike)
        return max(0.0, self.strike - spot)

    def payoff(self, spot: float) -> float:
        """Signed payoff of this leg at expiry, net of premium cash flow."""
        # Long pays premium (cash out); short collects it (cash in).
        return self.quantity * (self.intrinsic(spot) - self.premium)


def legs_payoff(legs: Sequence[OptionLeg], spot: float) -> float:
    """Total payoff of a multi-leg strategy at a single ``spot``."""
    return sum(leg.payoff(spot) for leg in legs)


def payoff_curve(spots: Sequence[float], fn: Callable[[float], float]) -> list[tuple[float, float]]:
    """Evaluate a single-arg payoff callable over a range of spot prices."""
    return [(s, fn(s)) for s in spots]


def price_grid(low: float, high: float, steps: int = 41) -> list[float]:
    """Evenly spaced underlying prices in ``[low, high]`` (inclusive)."""
    if steps < 2:
        raise ValueError("steps must be >= 2")
    if high <= low:
        raise ValueError("high must be greater than low")
    width = (high - low) / (steps - 1)
    return [low + width * i for i in range(steps)]
