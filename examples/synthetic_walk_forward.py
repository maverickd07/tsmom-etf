"""Deterministic integration example; synthetic results are not market evidence."""

import csv
from dataclasses import asdict
from datetime import date, timedelta
import io
import json
import math

from tsmom_etf.data import load_prices
from tsmom_etf.evaluation import evaluate_walk_forward


def synthetic_csv(sessions=120):
    """Generate two artificial series on weekday session labels, without randomness."""
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["date", "symbol", "adjusted_close"])
    day = date(2024, 1, 2)
    prices = {"EQUITY": 100.0, "BOND": 100.0}
    for i in range(sessions):
        while day.weekday() >= 5:
            day += timedelta(days=1)
        moves = {"EQUITY": .0004 + .009 * math.sin(i / 4),
                 "BOND": .0001 + .004 * math.cos(i / 7)}
        for symbol in prices:
            prices[symbol] *= 1 + moves[symbol]
            writer.writerow([day.isoformat(), symbol, format(prices[symbol], ".10f")])
        day += timedelta(days=1)
    return stream.getvalue()


def build_report():
    observations = load_prices(io.StringIO(synthetic_csv()))
    grouped = {}
    for observation in observations:
        grouped.setdefault(observation.date, {})[observation.symbol] = observation.adjusted_close
    panel = sorted(grouped.items())
    candidates = [5, 10, 20]
    folds = evaluate_walk_forward(panel, candidates, 60, 20, 10, cost_bps=5)
    results = []
    for fold in folds:
        results.append({
            "train_start": panel[fold.split.train.start][0].isoformat(),
            "train_end": panel[fold.split.train.stop - 1][0].isoformat(),
            "test_start": panel[fold.split.test.start][0].isoformat(),
            "test_end": panel[fold.split.test.stop - 1][0].isoformat(),
            "selected_lookback": fold.lookback,
            "strategy": asdict(fold.strategy),
            "buy_and_hold": asdict(fold.buy_and_hold),
            "cash": asdict(fold.cash)})
    # Predeclared fixed candidates are diagnostics, not an extra test-set selector.
    sensitivity = {
        str(candidate): [fold.strategy.total_return for fold in evaluate_walk_forward(
            panel, [candidate], 60, 20, 10, cost_bps=5)]
        for candidate in candidates}
    return {
        "data": "synthetic deterministic prices; not observed ETF performance",
        "assumptions": {"sessions": len(panel), "initial_cash": 10000,
                        "cost_bps": 5, "train_size": 60, "test_size": 20,
                        "vol_window": 10, "lookbacks": candidates,
                        "execution": "prior-close share sizing; next-close fill",
                        "folds": "independent cash resets; do not compound fold returns"},
        "folds": results,
        "fixed_lookback_sensitivity": sensitivity}


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, allow_nan=False))
