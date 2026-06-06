"""Implied-volatility solver.

Given a market option price, recover the Black-Scholes implied volatility. Uses
Newton-Raphson (driven by closed-form vega) with a robust bisection fallback so
it converges even when vega is tiny (deep ITM/OTM) or the initial guess is poor.

Part of Options Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

from options_trading_bot.bsm import OptionType, greeks, price

__all__ = ["IVError", "implied_volatility"]


class IVError(ValueError):
    """Raised when an implied volatility cannot be recovered for the inputs."""


def _intrinsic(spot: float, strike: float, t: float, r: float, option: OptionType) -> float:
    disc = math.exp(-r * t)
    if option is OptionType.CALL:
        return max(0.0, spot - strike * disc)
    return max(0.0, strike * disc - spot)


def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    t: float,
    r: float,
    option: OptionType = OptionType.CALL,
    *,
    initial_guess: float = 0.20,
    tol: float = 1e-8,
    max_iter: int = 100,
    vol_bounds: tuple[float, float] = (1e-6, 10.0),
) -> float:
    """Recover Black-Scholes implied volatility from a market price.

    Args:
        market_price: Observed option price.
        spot: Underlying price.
        strike: Strike price.
        t: Time to expiry in years (must be > 0).
        r: Risk-free rate (annualised).
        option: CALL or PUT.
        initial_guess: Starting volatility for Newton's method.
        tol: Absolute price tolerance for convergence.
        max_iter: Maximum Newton iterations before falling back to bisection.
        vol_bounds: Hard (low, high) bounds on volatility for the search.

    Returns:
        The annualised implied volatility.

    Raises:
        IVError: If ``t <= 0``, the price is below intrinsic / arbitrage-violating,
            or no volatility in ``vol_bounds`` reproduces ``market_price``.
    """
    if t <= 0:
        raise IVError("time to expiry must be positive to solve for IV")
    if market_price < 0:
        raise IVError("market price cannot be negative")

    lo, hi = vol_bounds
    intrinsic = _intrinsic(spot, strike, t, r, option)
    # Price must sit strictly between intrinsic value and the no-vol-cap upper bound.
    upper = price(spot, strike, t, r, hi, option)
    if market_price < intrinsic - tol:
        raise IVError("price below intrinsic value (arbitrage); no IV exists")
    if market_price > upper + tol:
        raise IVError("price above maximum achievable; no IV in bounds")

    vol = min(max(initial_guess, lo), hi)
    for _ in range(max_iter):
        model = price(spot, strike, t, r, vol, option)
        diff = model - market_price
        if abs(diff) < tol:
            return vol
        vega = greeks(spot, strike, t, r, vol, option).vega
        if vega < 1e-10:
            break  # vega too small for a stable Newton step -> bisection.
        step = diff / vega
        vol_new = vol - step
        if vol_new <= lo or vol_new >= hi or not math.isfinite(vol_new):
            break  # stepped out of bounds -> bisection.
        vol = vol_new

    # Bisection fallback: guaranteed to converge since price is monotone in vol.
    lo_b, hi_b = lo, hi
    for _ in range(200):
        mid = 0.5 * (lo_b + hi_b)
        diff = price(spot, strike, t, r, mid, option) - market_price
        if abs(diff) < tol:
            return mid
        if diff > 0:
            hi_b = mid
        else:
            lo_b = mid
    result = 0.5 * (lo_b + hi_b)
    if abs(price(spot, strike, t, r, result, option) - market_price) > 1e-4:
        raise IVError("failed to converge to an implied volatility")
    return result
