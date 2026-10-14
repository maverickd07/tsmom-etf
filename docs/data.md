# Price data contract

The input format is UTF-8 CSV with the columns `date`, `symbol`, and
`adjusted_close`. Each row represents one ETF observation at a daily close.

- `date`: trading-session date in ISO format (`YYYY-MM-DD`).
- `symbol`: nonempty, case-sensitive instrument identifier.
- `adjusted_close`: finite, strictly positive numeric price, consistently
  adjusted for splits and cash distributions by the selected provider.

Rows must be ordered by date within each symbol. A `(date, symbol)` pair may
occur only once. Different symbols may share a date. Missing observations are
omitted rather than represented as zero prices. Never backfill prices using
future observations; downstream calculations must explicitly choose how to
handle gaps and differing trading calendars.

All instruments in a portfolio must use a common valuation currency. Currency
conversion, if needed, must happen before portfolio accounting and document
the FX source and timing. Prices are not assumed to be executable fills.

## Timing and provenance

A close observed on session t can inform a decision after that close. A
position based on it must not earn the return ending on session t. The
backtest must explicitly state the subsequent execution convention.

Keep a sidecar provenance record for each dataset: provider, download time,
symbols, requested date range, currency, adjustment convention, and known
gaps. Historical adjusted prices may be revised; preserve the actual input
snapshot used for each experiment. Raw datasets belong in `data/`, which is
excluded from version control.

## Example

```csv
date,symbol,adjusted_close
2024-01-02,SPY,470.00
2024-01-02,TLT,95.00
2024-01-03,SPY,468.00
2024-01-03,TLT,94.50
```

These prices are illustrative synthetic values, not market observations.
