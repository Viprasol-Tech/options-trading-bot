"""Tests for the implied-volatility solver.

The core property: pricing at a known vol and then solving for IV must recover
that vol (round-trip). We also cover the bisection fallback and error paths.
"""

from __future__ import annotations

import math

import pytest

from options_trading_bot.bsm import OptionType, price
from options_trading_bot.iv import IVError, implied_volatility


@pytest.mark.parametrize("true_vol", [0.05, 0.15, 0.30, 0.75, 1.5])
@pytest.mark.parametrize("option", [OptionType.CALL, OptionType.PUT])
def test_iv_round_trip(true_vol: float, option: OptionType) -> None:
    s, k, t, r = 100.0, 105.0, 0.5, 0.03
    mkt = price(s, k, t, r, true_vol, option)
    solved = implied_volatility(mkt, s, k, t, r, option)
    assert math.isclose(solved, true_vol, abs_tol=1e-5)


def test_iv_deep_itm_uses_fallback() -> None:
    # Deep ITM call: tiny vega, Newton struggles -> bisection must still converge.
    s, k, t, r, true_vol = 200.0, 100.0, 0.25, 0.01, 0.40
    mkt = price(s, k, t, r, true_vol, OptionType.CALL)
    solved = implied_volatility(mkt, s, k, t, r, OptionType.CALL, initial_guess=0.9)
    assert math.isclose(solved, true_vol, abs_tol=1e-4)


def test_iv_recovers_with_bad_initial_guess() -> None:
    s, k, t, r, true_vol = 100.0, 100.0, 1.0, 0.05, 0.22
    mkt = price(s, k, t, r, true_vol, OptionType.CALL)
    solved = implied_volatility(mkt, s, k, t, r, OptionType.CALL, initial_guess=5.0)
    assert math.isclose(solved, true_vol, abs_tol=1e-5)


def test_iv_below_intrinsic_raises() -> None:
    with pytest.raises(IVError):
        # Price below discounted intrinsic for a deep ITM call is arbitrage.
        implied_volatility(0.01, 200.0, 100.0, 0.5, 0.0, OptionType.CALL)


def test_iv_requires_positive_time() -> None:
    with pytest.raises(IVError):
        implied_volatility(5.0, 100.0, 100.0, 0.0, 0.05, OptionType.CALL)


def test_iv_negative_price_raises() -> None:
    with pytest.raises(IVError):
        implied_volatility(-1.0, 100.0, 100.0, 0.5, 0.05, OptionType.CALL)
