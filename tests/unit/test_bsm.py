"""Tests for Black-Scholes pricing, Greeks, and payoffs.

These check against known properties: put-call parity, delta bounds, and a
reference ATM price, which together pin down a correct implementation.
"""

from __future__ import annotations

import math

from options_trading_bot.bsm import OptionType, greeks, price
from options_trading_bot.payoff import covered_call, long_straddle, option_payoff


def test_atm_call_reference_value() -> None:
    # S=K=100, T=1y, r=0, vol=20% -> known BSM call ≈ 7.9656.
    p = price(100, 100, 1.0, 0.0, 0.20, OptionType.CALL)
    assert math.isclose(p, 7.9656, abs_tol=1e-3)


def test_put_call_parity() -> None:
    s, k, t, r, vol = 100.0, 95.0, 0.5, 0.03, 0.25
    call = price(s, k, t, r, vol, OptionType.CALL)
    put = price(s, k, t, r, vol, OptionType.PUT)
    # C - P == S - K*e^{-rT}
    assert math.isclose(call - put, s - k * math.exp(-r * t), abs_tol=1e-6)


def test_call_delta_between_0_and_1() -> None:
    g = greeks(100, 100, 0.5, 0.02, 0.3, OptionType.CALL)
    assert 0.0 <= g.delta <= 1.0
    assert g.gamma > 0
    assert g.vega > 0


def test_put_delta_negative() -> None:
    g = greeks(100, 100, 0.5, 0.02, 0.3, OptionType.PUT)
    assert -1.0 <= g.delta <= 0.0


def test_expiry_is_intrinsic() -> None:
    assert price(110, 100, 0.0, 0.05, 0.2, OptionType.CALL) == 10.0
    assert price(90, 100, 0.0, 0.05, 0.2, OptionType.PUT) == 10.0


def test_payoffs() -> None:
    assert option_payoff(110, 100, OptionType.CALL, premium=4) == 6.0
    # Covered call caps upside at strike + premium - entry.
    assert math.isclose(covered_call(120, 100, 110, 3), 13.0)
    # Straddle profits on a big move.
    assert long_straddle(130, 100, 5, 5) > 0
