"""Options Trading Bot - Black-Scholes pricing, Greeks, IV & strategies by Viprasol Tech."""

from __future__ import annotations

from options_trading_bot.bsm import Greeks, OptionType, greeks, price
from options_trading_bot.iv import IVError, implied_volatility
from options_trading_bot.payoff import OptionLeg, legs_payoff, option_payoff, price_grid
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

__version__ = "0.2.0"
__author__ = "Viprasol Tech Private Limited"
__all__ = [
    "Greeks",
    "IVError",
    "OptionLeg",
    "OptionType",
    "Strategy",
    "__version__",
    "bear_call_spread",
    "bear_put_spread",
    "bull_call_spread",
    "bull_put_spread",
    "greeks",
    "implied_volatility",
    "iron_condor",
    "legs_payoff",
    "long_call_butterfly",
    "long_strangle",
    "option_payoff",
    "price",
    "price_grid",
]
