# tsmom-etf

Time-series momentum research on a liquid multi-asset ETF universe, with
walk-forward evaluation, transaction costs, and transparent diagnostics.

## Status

Package scaffold and input data conventions are in place. No strategy results
have been produced yet.

## Development setup

Python 3.9 or newer is required. From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

See [the price data contract](docs/data.md) for input and timing conventions.

## Research scope

- Daily adjusted prices for a configurable ETF universe.
- Momentum signals based only on information available at the decision time.
- Positions applied no earlier than the following trading period.
- Explicit turnover, transaction costs, and volatility targeting.
- Chronological walk-forward evaluation against simple benchmarks.
- Reproducible reports covering returns, drawdowns, exposure, and sensitivity.

## Development roadmap

- [x] Define input data conventions and a minimal Python package.
- [x] Validate prices, missing observations, and date ordering.
- [ ] Implement lagged momentum signals with synthetic-data tests.
- [ ] Implement portfolio accounting, turnover, and costs.
- [ ] Add volatility targeting and exposure limits.
- [ ] Add chronological walk-forward evaluation and benchmarks.
- [ ] Add diagnostics and a reproducible example.

This repository is research software. Results should document assumptions,
data limitations, and the distinction between historical tests and live trading.

## Input validation

`tsmom_etf.data.load_prices` accepts an open CSV text stream and returns
validated observations without filling gaps. Invalid rows raise `ValueError`
with a line number. Run the synthetic data tests with:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```
