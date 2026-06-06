"""Common multi-leg option strategies.

Each builder returns a :class:`Strategy` — an ordered set of :class:`OptionLeg`
objects with helpers for expiry payoff, break-evens, max profit/loss, net cash
flow, and aggregate ("position") Greeks. Strategies covered:

- Vertical spreads: bull call, bear put (debit) and bull put, bear call (credit)
- Iron condor (defined-risk, neutral)
- Butterfly (long call butterfly, pinned to a strike)
- Strangle (long, OTM call + OTM put)

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import pairwise

from options_trading_bot.bsm import Greeks, OptionType, greeks
from options_trading_bot.payoff import OptionLeg, legs_payoff, price_grid

__all__ = [
    "Strategy",
    "bear_call_spread",
    "bear_put_spread",
    "bull_call_spread",
    "bull_put_spread",
    "iron_condor",
    "long_call_butterfly",
    "long_strangle",
]


@dataclass(slots=True, frozen=True)
class Strategy:
    """A named multi-leg option strategy with analytics helpers."""

    name: str
    legs: tuple[OptionLeg, ...] = field(default_factory=tuple)

    def payoff(self, spot: float) -> float:
        """Net payoff at expiry for a single underlying price."""
        return legs_payoff(self.legs, spot)

    def net_premium(self) -> float:
        """Net cash flow at entry.

        Negative => net debit (you pay); positive => net credit (you collect).
        """
        return -sum(leg.quantity * leg.premium for leg in self.legs)

    def payoff_curve(self, low: float, high: float, steps: int = 41) -> list[tuple[float, float]]:
        """Payoff sampled across an evenly spaced price grid."""
        return [(s, self.payoff(s)) for s in price_grid(low, high, steps)]

    def break_evens(self, low: float, high: float, steps: int = 401) -> list[float]:
        """Approximate break-even underlying prices via sign changes on a fine grid.

        Crossings within a small tolerance of one another are merged so an exact
        grid-point zero is not double-counted with its neighbouring interpolation.
        """
        grid = price_grid(low, high, steps)
        spacing = grid[1] - grid[0]
        crossings: list[float] = []
        prev_s = grid[0]
        prev_p = self.payoff(prev_s)
        for s in grid[1:]:
            p = self.payoff(s)
            if prev_p == 0.0:
                crossings.append(prev_s)
            elif (prev_p < 0) != (p < 0):
                # Linear interpolation of the zero crossing.
                frac = prev_p / (prev_p - p)
                crossings.append(prev_s + frac * (s - prev_s))
            prev_s, prev_p = s, p

        out: list[float] = []
        for c in crossings:
            if not out or abs(c - out[-1]) > spacing * 0.5:
                out.append(c)
        return out

    def max_profit(self, low: float, high: float, steps: int = 401) -> float:
        """Maximum payoff observed across the price grid."""
        return max(p for _, p in self.payoff_curve(low, high, steps))

    def max_loss(self, low: float, high: float, steps: int = 401) -> float:
        """Minimum (most negative) payoff observed across the price grid."""
        return min(p for _, p in self.payoff_curve(low, high, steps))

    def position_greeks(self, spot: float, t: float, r: float, vol: float) -> Greeks:
        """Aggregate Greeks of the whole position at ``spot`` (quantity-weighted)."""
        d = g = v = th = rho = 0.0
        for leg in self.legs:
            lg = greeks(spot, leg.strike, t, r, vol, leg.option)
            d += leg.quantity * lg.delta
            g += leg.quantity * lg.gamma
            v += leg.quantity * lg.vega
            th += leg.quantity * lg.theta
            rho += leg.quantity * lg.rho
        return Greeks(delta=d, gamma=g, vega=v, theta=th, rho=rho)


def _check_order(*strikes: float) -> None:
    for a, b in pairwise(strikes):
        if not a < b:
            raise ValueError(f"strikes must be strictly increasing, got {strikes}")


def bull_call_spread(
    lower_strike: float, upper_strike: float, lower_premium: float, upper_premium: float
) -> Strategy:
    """Long lower-strike call, short upper-strike call (a debit spread)."""
    _check_order(lower_strike, upper_strike)
    return Strategy(
        "bull_call_spread",
        (
            OptionLeg(OptionType.CALL, lower_strike, 1.0, lower_premium),
            OptionLeg(OptionType.CALL, upper_strike, -1.0, upper_premium),
        ),
    )


def bear_put_spread(
    lower_strike: float, upper_strike: float, lower_premium: float, upper_premium: float
) -> Strategy:
    """Long upper-strike put, short lower-strike put (a debit spread)."""
    _check_order(lower_strike, upper_strike)
    return Strategy(
        "bear_put_spread",
        (
            OptionLeg(OptionType.PUT, upper_strike, 1.0, upper_premium),
            OptionLeg(OptionType.PUT, lower_strike, -1.0, lower_premium),
        ),
    )


def bull_put_spread(
    lower_strike: float, upper_strike: float, lower_premium: float, upper_premium: float
) -> Strategy:
    """Short upper-strike put, long lower-strike put (a credit spread)."""
    _check_order(lower_strike, upper_strike)
    return Strategy(
        "bull_put_spread",
        (
            OptionLeg(OptionType.PUT, upper_strike, -1.0, upper_premium),
            OptionLeg(OptionType.PUT, lower_strike, 1.0, lower_premium),
        ),
    )


def bear_call_spread(
    lower_strike: float, upper_strike: float, lower_premium: float, upper_premium: float
) -> Strategy:
    """Short lower-strike call, long upper-strike call (a credit spread)."""
    _check_order(lower_strike, upper_strike)
    return Strategy(
        "bear_call_spread",
        (
            OptionLeg(OptionType.CALL, lower_strike, -1.0, lower_premium),
            OptionLeg(OptionType.CALL, upper_strike, 1.0, upper_premium),
        ),
    )


def iron_condor(
    put_long: float,
    put_short: float,
    call_short: float,
    call_long: float,
    premiums: Sequence[float],
) -> Strategy:
    """Defined-risk neutral strategy: a bull put spread + a bear call spread.

    Args:
        put_long: Strike of the long (protective) put — the lowest strike.
        put_short: Strike of the short put.
        call_short: Strike of the short call.
        call_long: Strike of the long (protective) call — the highest strike.
        premiums: Four premiums in strike order
            ``(put_long, put_short, call_short, call_long)``.
    """
    _check_order(put_long, put_short, call_short, call_long)
    if len(premiums) != 4:
        raise ValueError("iron_condor needs exactly 4 premiums in strike order")
    p_pl, p_ps, p_cs, p_cl = premiums
    return Strategy(
        "iron_condor",
        (
            OptionLeg(OptionType.PUT, put_long, 1.0, p_pl),
            OptionLeg(OptionType.PUT, put_short, -1.0, p_ps),
            OptionLeg(OptionType.CALL, call_short, -1.0, p_cs),
            OptionLeg(OptionType.CALL, call_long, 1.0, p_cl),
        ),
    )


def long_call_butterfly(
    lower: float,
    middle: float,
    upper: float,
    premiums: Sequence[float],
) -> Strategy:
    """Long call butterfly: +1 lower, -2 middle, +1 upper call.

    Strikes should be equally spaced for the classic symmetric payoff, but any
    strictly increasing triple is accepted.

    Args:
        lower: Lowest strike (long).
        middle: Body strike (short x2).
        upper: Highest strike (long).
        premiums: Three premiums in strike order ``(lower, middle, upper)``.
    """
    _check_order(lower, middle, upper)
    if len(premiums) != 3:
        raise ValueError("long_call_butterfly needs exactly 3 premiums in strike order")
    p_lo, p_mid, p_hi = premiums
    return Strategy(
        "long_call_butterfly",
        (
            OptionLeg(OptionType.CALL, lower, 1.0, p_lo),
            OptionLeg(OptionType.CALL, middle, -2.0, p_mid),
            OptionLeg(OptionType.CALL, upper, 1.0, p_hi),
        ),
    )


def long_strangle(
    put_strike: float,
    call_strike: float,
    put_premium: float,
    call_premium: float,
) -> Strategy:
    """Long OTM put + long OTM call (profits on a large move in either direction)."""
    _check_order(put_strike, call_strike)
    return Strategy(
        "long_strangle",
        (
            OptionLeg(OptionType.PUT, put_strike, 1.0, put_premium),
            OptionLeg(OptionType.CALL, call_strike, 1.0, call_premium),
        ),
    )
