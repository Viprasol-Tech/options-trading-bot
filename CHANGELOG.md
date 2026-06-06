# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- **Implied-volatility solver** (`implied_volatility`): Newton-Raphson driven by
  closed-form vega with a guaranteed bisection fallback for deep ITM/OTM options
  and poor initial guesses; raises `IVError` on arbitrage-violating inputs.
- **Multi-leg strategy engine** (`strategies` module): a composable `OptionLeg`
  primitive and a `Strategy` class with expiry payoff, net premium (debit/credit),
  break-evens, max profit/loss, and quantity-weighted **position Greeks**.
- **New strategy builders**: bull call / bear put (debit) and bull put / bear call
  (credit) vertical spreads, iron condor, long call butterfly, and long strangle.
- **Payoff-plot data exporter** (`export` module): render any strategy's payoff
  curve to CSV or JSON (string or file) for matplotlib/Excel/web charts, with
  metadata (break-evens, max P/L) in the JSON form.
- **New CLI subcommands**: `iv` (solve implied volatility), `strategy` (analyse a
  named multi-leg strategy), and `export` (write a payoff curve to disk).
- `price_grid` helper and `examples/quickstart.py` end-to-end walkthrough.
- Test suite expanded from 6 to 47 tests covering IV round-trips, strategy payoff
  shapes, exporter output, and every CLI subcommand.

### Changed
- `payoff` module now exposes `OptionLeg`, `legs_payoff`, and `price_grid` and is
  the shared foundation for the strategy engine.
- Bumped version to 0.2.0.

## [0.1.0] - 2025

### Added
- Initial release of options-trading-bot: Black-Scholes pricing, Greeks, and
  strategy payoffs.
