"""Tests for multi-leg strategies: payoff shape, break-evens, and risk bounds."""

from __future__ import annotations

import math

import pytest

from options_trading_bot.bsm import OptionType
from options_trading_bot.payoff import OptionLeg
from options_trading_bot.strategies import (
    bear_call_spread,
    bull_call_spread,
    iron_condor,
    long_call_butterfly,
    long_strangle,
)


def test_bull_call_spread_capped_payoff() -> None:
    # Long 95 call @7, short 105 call @2.5 -> net debit 4.5, max width 10.
    strat = bull_call_spread(95.0, 105.0, 7.0, 2.5)
    assert math.isclose(strat.net_premium(), -4.5)
    # Below both strikes -> lose net debit.
    assert math.isclose(strat.payoff(80.0), -4.5)
    # Above upper strike -> capped at width - debit = 10 - 4.5 = 5.5.
    assert math.isclose(strat.payoff(120.0), 5.5)
    assert math.isclose(strat.max_profit(70.0, 130.0), 5.5, abs_tol=1e-6)
    assert math.isclose(strat.max_loss(70.0, 130.0), -4.5, abs_tol=1e-6)


def test_bull_call_spread_break_even() -> None:
    strat = bull_call_spread(95.0, 105.0, 7.0, 2.5)
    # Break-even = lower strike + net debit = 95 + 4.5 = 99.5.
    bes = strat.break_evens(70.0, 130.0)
    assert len(bes) == 1
    assert math.isclose(bes[0], 99.5, abs_tol=0.1)


def test_credit_spread_is_credit() -> None:
    strat = bear_call_spread(95.0, 105.0, 7.0, 2.5)
    # Short 95 @7, long 105 @2.5 -> net credit 4.5.
    assert math.isclose(strat.net_premium(), 4.5)
    # Far above strikes -> max loss = -(width - credit) = -(10 - 4.5) = -5.5.
    assert math.isclose(strat.payoff(130.0), -5.5)


def test_iron_condor_neutral_profile() -> None:
    strat = iron_condor(90.0, 95.0, 105.0, 110.0, (1.0, 2.5, 2.5, 1.0))
    # Net credit = (2.5 + 2.5) - (1.0 + 1.0) = 3.0.
    assert math.isclose(strat.net_premium(), 3.0)
    # Inside the short strikes -> keep full credit.
    assert math.isclose(strat.payoff(100.0), 3.0)
    # Two break-evens, one on each wing.
    bes = strat.break_evens(70.0, 130.0)
    assert len(bes) == 2
    assert bes[0] < 95.0 < 105.0 < bes[1]
    # Max loss = -(wing width - credit) = -(5 - 3) = -2.
    assert math.isclose(strat.max_loss(70.0, 130.0), -2.0, abs_tol=1e-6)


def test_butterfly_peaks_at_body() -> None:
    strat = long_call_butterfly(95.0, 100.0, 105.0, (7.0, 3.5, 1.2))
    # Net debit = 7.0 - 2*3.5 + 1.2 = 1.2.
    assert math.isclose(strat.net_premium(), -1.2)
    peak = strat.payoff(100.0)
    # Peak (at body) beats the wings.
    assert peak > strat.payoff(95.0)
    assert peak > strat.payoff(105.0)
    # Max profit ~= body width - debit = 5 - 1.2 = 3.8.
    assert math.isclose(strat.max_profit(80.0, 120.0), 3.8, abs_tol=1e-6)


def test_strangle_profits_on_big_move() -> None:
    strat = long_strangle(95.0, 105.0, 2.0, 2.0)
    assert math.isclose(strat.net_premium(), -4.0)
    assert strat.payoff(70.0) > 0  # big down move
    assert strat.payoff(130.0) > 0  # big up move
    assert math.isclose(strat.payoff(100.0), -4.0)  # pinned -> lose both premiums


def test_position_greeks_aggregate() -> None:
    strat = bull_call_spread(95.0, 105.0, 7.0, 2.5)
    g = strat.position_greeks(100.0, 0.25, 0.03, 0.25)
    # Long lower call dominates -> net positive delta, bounded by 1.
    assert 0.0 < g.delta < 1.0


def test_strikes_must_increase() -> None:
    with pytest.raises(ValueError):
        bull_call_spread(105.0, 95.0, 7.0, 2.5)


def test_iron_condor_premium_count_validated() -> None:
    with pytest.raises(ValueError):
        iron_condor(90.0, 95.0, 105.0, 110.0, (1.0, 2.5, 2.5))


def test_option_leg_short_payoff_sign() -> None:
    short_call = OptionLeg(OptionType.CALL, 100.0, -1.0, 3.0)
    # Short call: collect 3 premium, pay intrinsic above strike.
    assert math.isclose(short_call.payoff(100.0), 3.0)
    assert math.isclose(short_call.payoff(110.0), 3.0 - 10.0)
