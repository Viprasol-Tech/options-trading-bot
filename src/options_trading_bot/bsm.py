"""Black-Scholes-Merton option pricing and Greeks.

Implemented with only the standard library (``math.erf`` for the normal CDF), so
there are no heavy numerical dependencies. Covers European calls and puts plus
the primary Greeks: delta, gamma, vega, theta, rho.

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class OptionType(str, Enum):
    """Option right."""

    CALL = "call"
    PUT = "put"


def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _d1_d2(spot: float, strike: float, t: float, r: float, vol: float) -> tuple[float, float]:
    d1 = (math.log(spot / strike) + (r + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    return d1, d2


def price(
    spot: float,
    strike: float,
    t: float,
    r: float,
    vol: float,
    option: OptionType = OptionType.CALL,
) -> float:
    """Black-Scholes price of a European option.

    Args:
        spot: Underlying price.
        strike: Strike price.
        t: Time to expiry in years.
        r: Risk-free rate (annualised, e.g. 0.05).
        vol: Implied volatility (annualised, e.g. 0.20).
        option: CALL or PUT.
    """
    if t <= 0 or vol <= 0:
        intrinsic = spot - strike if option is OptionType.CALL else strike - spot
        return max(0.0, intrinsic)
    d1, d2 = _d1_d2(spot, strike, t, r, vol)
    disc = math.exp(-r * t)
    if option is OptionType.CALL:
        return spot * _norm_cdf(d1) - strike * disc * _norm_cdf(d2)
    return strike * disc * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


@dataclass(slots=True, frozen=True)
class Greeks:
    """The primary option Greeks."""

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def greeks(
    spot: float,
    strike: float,
    t: float,
    r: float,
    vol: float,
    option: OptionType = OptionType.CALL,
) -> Greeks:
    """Compute the primary Greeks (per 1.0 move; vega/rho per 1.00 = 100%)."""
    if t <= 0 or vol <= 0:
        return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
    d1, d2 = _d1_d2(spot, strike, t, r, vol)
    disc = math.exp(-r * t)
    sqrt_t = math.sqrt(t)
    gamma = _norm_pdf(d1) / (spot * vol * sqrt_t)
    vega = spot * _norm_pdf(d1) * sqrt_t
    if option is OptionType.CALL:
        delta = _norm_cdf(d1)
        theta = -(spot * _norm_pdf(d1) * vol) / (2 * sqrt_t) - r * strike * disc * _norm_cdf(d2)
        rho = strike * t * disc * _norm_cdf(d2)
    else:
        delta = _norm_cdf(d1) - 1.0
        theta = -(spot * _norm_pdf(d1) * vol) / (2 * sqrt_t) + r * strike * disc * _norm_cdf(-d2)
        rho = -strike * t * disc * _norm_cdf(-d2)
    return Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)
