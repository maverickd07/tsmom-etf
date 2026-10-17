"""Chronological walk-forward splits with disjoint evaluation windows."""

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List

from .diagnostics import PerformanceSummary


@dataclass(frozen=True)
class WalkForwardSplit:
    train: slice
    test: slice


def walk_forward_splits(
    dates: Iterable[date], train_size: int, test_size: int,
    gap: int = 0, expanding: bool = False,
) -> List[WalkForwardSplit]:
    """Return half-open row slices for complete chronological test blocks.

    Training always precedes testing. Gap excludes rows immediately before
    each test block. Test blocks never overlap; incomplete final blocks are
    omitted. Rolling training has train_size rows; expanding training starts
    at row zero and uses train_size as its initial size. No model is fit here.
    """
    for name, value, minimum in (("train_size", train_size, 1),
                                 ("test_size", test_size, 1), ("gap", gap, 0)):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(name + " has an invalid size")
    if not isinstance(expanding, bool):
        raise ValueError("expanding must be a boolean")
    ordered = list(dates)
    if any(type(day) is not date for day in ordered):
        raise ValueError("dates must be daily date objects")
    if any(b <= a for a, b in zip(ordered, ordered[1:])):
        raise ValueError("dates must strictly increase without duplicates")
    splits = []
    for start in range(train_size + gap, len(ordered) - test_size + 1, test_size):
        train_stop = start - gap
        train_start = 0 if expanding else train_stop - train_size
        splits.append(WalkForwardSplit(slice(train_start, train_stop),
                                       slice(start, start + test_size)))
    return splits


@dataclass(frozen=True)
class FoldEvaluation:
    split: WalkForwardSplit
    lookback: int
    strategy: "PerformanceSummary"
    buy_and_hold: "PerformanceSummary"
    cash: "PerformanceSummary"


def evaluate_walk_forward(
    prices: Iterable[tuple], lookbacks: Iterable[int], train_size: int,
    test_size: int, vol_window: int, gap: int = 0, expanding: bool = False,
    initial_cash: float = 10000.0, cost_bps: float = 0.0,
) -> List[FoldEvaluation]:
    """Select lookback by training net return, then freeze it for each test.

    Ties follow candidate input order. Each fold starts with fresh cash and
    independent holdings; fold returns must not be treated as a continuous
    portfolio. Earlier prices (including gap rows) warm test features, but no
    positions or P&L carry from training. Test features update causally as new
    closes arrive. All three portfolios share test dates and initial capital.
    """
    from .accounting import account_portfolio
    from .benchmarks import cash_benchmark, equal_weight_buy_and_hold
    from .diagnostics import summarize_performance
    from .signals import lagged_momentum
    from .strategy import run_momentum

    rows = [(day, dict(panel)) for day, panel in prices]
    account_portfolio(rows, {}, initial_cash, cost_bps)
    candidates = list(lookbacks)
    if not candidates:
        raise ValueError("at least one lookback candidate is required")
    for lookback in candidates:
        lagged_momentum([], lookback)
    run_momentum([], candidates[0], vol_window, initial_cash, cost_bps)
    splits = walk_forward_splits([day for day, _ in rows], train_size, test_size, gap, expanding)
    if train_size < max(max(candidates), vol_window) + 3:
        raise ValueError("training needs warmup, a fill, and a subsequent return")
    results = []
    for split in splits:
        training = rows[split.train]
        scores = []
        for lookback in candidates:
            ledger = run_momentum(training, lookback, vol_window, initial_cash, cost_bps)
            scores.append(summarize_performance(ledger, initial_cash).total_return)
        chosen = candidates[max(range(len(candidates)), key=lambda i: scores[i])]
        context = rows[split.train.start:split.test.stop]
        start = split.test.start - split.train.start
        ledger = run_momentum(context, chosen, vol_window, initial_cash, cost_bps,
                              trade_start=start)[start:]
        test_rows = rows[split.test]
        results.append(FoldEvaluation(
            split, chosen, summarize_performance(ledger, initial_cash),
            summarize_performance(equal_weight_buy_and_hold(test_rows, initial_cash, cost_bps), initial_cash),
            summarize_performance(cash_benchmark(test_rows, initial_cash), initial_cash)))
    return results
