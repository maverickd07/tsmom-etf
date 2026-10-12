# tsmom-etf

Time-series momentum research on a liquid multi-asset ETF universe, with
walk-forward evaluation, transaction costs, and transparent diagnostics.

## Status

Initial planning stage. No strategy results have been produced yet.

## Research scope

- Daily adjusted prices for a configurable ETF universe.
- Momentum signals based only on information available at the decision time.
- Positions applied no earlier than the following trading period.
- Explicit turnover, transaction costs, and volatility targeting.
- Chronological walk-forward evaluation against simple benchmarks.
- Reproducible reports covering returns, drawdowns, exposure, and sensitivity.

## Development roadmap

- [ ] Define input data conventions and a minimal Python package.
- [ ] Validate prices, missing observations, and date ordering.
- [ ] Implement lagged momentum signals with synthetic-data tests.
- [ ] Implement portfolio accounting, turnover, and costs.
- [ ] Add volatility targeting and exposure limits.
- [ ] Add chronological walk-forward evaluation and benchmarks.
- [ ] Add diagnostics and a reproducible example.

This repository is research software. Results should document assumptions,
data limitations, and the distinction between historical tests and live trading.
