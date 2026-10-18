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
- [x] Implement lagged momentum signals with synthetic-data tests.
- [x] Implement portfolio accounting, turnover, and costs.
- [x] Add volatility targeting and exposure limits.
- [x] Add chronological walk-forward evaluation and benchmarks.
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

## Momentum signals

`tsmom_etf.signals.lagged_momentum(observations, lookback)` compares the
previous close with the close `lookback` observed intervals earlier, separately
for each symbol. It returns +1, -1, or 0; warmup observations return `None`.
The current close cannot affect its own signal. Lookback counts observations,
so gaps do not create synthetic prices or imply a fixed calendar horizon.

Signals are directions, not executable orders. Portfolio accounting must
state its fill convention and must not attribute returns preceding execution
to a newly calculated signal.

## Portfolio accounting

`tsmom_etf.accounting.account_portfolio` accepts a synchronized price panel
and explicit share holdings executed at dated closes. Existing holdings earn
the move into each close; trades then update cash and incur proportional
costs on absolute traded notional (buys plus sells). Unchanged share targets
incur no turnover. Missing symbols in a target are liquidated; absent target
dates retain existing holdings. Missing price rows are rejected rather than
silently filled. Results include gross P&L, traded notional, costs, cash, and
equity. Traded notional divided by initial capital is fixed-capital turnover.

The caller must supply orders known before their fill. This ledger does not
convert signals to executable orders or model fill delays. Adjusted prices
and share quantities represent synthetic total-return units. Short positions
and borrowing are permitted, but financing, borrow fees, cash interest, and
execution slippage beyond the configured basis-point charge are excluded.

## Risk controls

`tsmom_etf.risk.lagged_volatility_scale` estimates annualized sample volatility
from a rolling window of prior simple returns. It excludes the current return,
returns `None` during warmup, caps per-asset exposure, and assigns zero exposure
when measured volatility is zero. The default annualization is 252 equally
spaced sessions per year; this is an assumption, not a calendar-gap repair.

Multiply each scale by an already available momentum direction, then use
`cap_gross_exposure` to proportionally constrain the sum of absolute portfolio
weights. Per-asset scaling alone does not target portfolio volatility because
it ignores asset correlations. These functions produce research weights;
execution timing, conversion to shares, and trading costs remain explicit
responsibilities of the backtest integration.

## Walk-forward splits

`tsmom_etf.evaluation.walk_forward_splits` returns half-open training and test
row slices over unique, increasing session dates. It supports rolling or
expanding training, an optional gap, and nonoverlapping complete test blocks;
a partial trailing block is omitted. Sizes and gaps count observed sessions.

Fit or select parameters using only each training slice, freeze the selection,
then evaluate its test slice. Later training windows may include earlier test
data, as it would then be historical. The splitter does not itself fit models,
compute benchmarks, or prevent leakage inside caller-provided feature code.

## Benchmarks

`tsmom_etf.benchmarks.equal_weight_buy_and_hold` invests equal notional amounts
at the first close and holds fixed fractional shares thereafter. Entry costs
are reserved from capital, weights drift with prices, and open holdings are
marked to market without assumed final liquidation. `cash_benchmark` holds
cash with zero interest. Both use the strategy accounting ledger and validate
the synchronized price panel. Compare strategies over identical evaluation
dates, capital, and cost assumptions; these helpers do not select parameters
or run walk-forward evaluation themselves.

## Performance diagnostics

`tsmom_etf.diagnostics.summarize_performance` reports net total return,
nonpositive maximum drawdown, annualized sample volatility, total costs, and
traded notional divided by initial capital. Initial capital anchors return
and drawdown so entry fees remain visible. Volatility uses subsequent
close-to-close returns with an explicit sessions-per-year assumption; it is
undefined (`None`) with fewer than two intervals. Nonpositive equity is
rejected. These summaries do not infer risk-free rates, financing costs, or
statistical significance and do not replace out-of-sample evaluation.

## Strategy execution

`tsmom_etf.strategy.run_momentum` connects lagged directions, prior-return
volatility scaling, gross-weight limits, and the cost ledger. Orders are sized
in shares using the preceding close and fixed initial capital, filled at the
next close, and earn returns only after that fill. Capital is not compounded
into new order sizes. Warmup and zero-volatility periods target zero holdings.

Exposure limits apply at order sizing; intervening price moves can exceed
those limits at execution. This daily close model allows shorts and negative
cash, omits financing and borrow fees, and assumes fractional adjusted-price
units. It is a reproducible research convention, not an execution simulator.

## Walk-forward comparison

`evaluate_walk_forward` in `tsmom_etf.evaluation` selects a momentum lookback
using only training net returns, then freezes that parameter for the next
complete test block. Candidate order breaks ties. Each test starts from cash,
uses earlier prices for causal feature warmup, and compares the strategy,
equal-weight buy-and-hold, and cash on identical dates. Trading costs apply
to strategy and buy-and-hold entries. Gap rows may warm features but do not
contribute to training scores or test P&L.

Folds reset capital and holdings; their summaries are independent experiments,
not a stitched equity curve. This small grid search does not correct for
multiple testing. Keep a separate untouched holdout for final research claims.

## Reproducible example

Run the deterministic two-asset integration example from the repository root:

```sh
PYTHONPATH=src python3 examples/synthetic_walk_forward.py
```

It generates artificial equity-like and bond-like price series, round-trips
through the CSV validator, and prints a JSON report with three independent
walk-forward folds, matched benchmarks, costs, drawdowns, and fixed-lookback
sensitivity. The predeclared sensitivity grid is descriptive; do not choose
a winner from test outcomes and present it as untouched out-of-sample evidence.
Weekday labels do not model exchange holidays. These synthetic results verify
software behavior and say nothing about achievable ETF returns. For real data,
provide a documented common-currency adjusted-price snapshot and resolve
calendar gaps explicitly before annualizing statistics.
