from datetime import date, timedelta
import math
import unittest

from tsmom_etf.accounting import PortfolioStep
from tsmom_etf.benchmarks import cash_benchmark, equal_weight_buy_and_hold
from tsmom_etf.diagnostics import summarize_performance


def snapshots(equities):
    return [PortfolioStep(date(2024, 1, 1) + timedelta(days=i), 0, 0, 0, e, e)
            for i, e in enumerate(equities)]


class DiagnosticTests(unittest.TestCase):
    def test_return_drawdown_and_sample_volatility(self):
        summary = summarize_performance(snapshots([100, 120, 90]), 100, 1)
        self.assertAlmostEqual(summary.total_return, -.1)
        self.assertAlmostEqual(summary.max_drawdown, -.25)
        self.assertAlmostEqual(summary.annualized_volatility, .45 / math.sqrt(2))

    def test_entry_fee_counts_in_return_and_drawdown(self):
        rows = [(date(2024, 1, 1), {"A": 100})]
        summary = summarize_performance(equal_weight_buy_and_hold(rows, 100, 100), 100)
        self.assertAlmostEqual(summary.total_return, 1 / 1.01 - 1)
        self.assertAlmostEqual(summary.max_drawdown, summary.total_return)
        self.assertAlmostEqual(summary.total_cost, 100 - 100 / 1.01)
        self.assertAlmostEqual(summary.turnover_on_initial_capital, 1 / 1.01)
        self.assertIsNone(summary.annualized_volatility)

    def test_cash_is_flat(self):
        rows = [(s.date, {"A": 100}) for s in snapshots([1, 1, 1])]
        summary = summarize_performance(cash_benchmark(rows, 100), 100)
        self.assertEqual(summary.total_return, 0)
        self.assertEqual(summary.max_drawdown, 0)
        self.assertEqual(summary.annualized_volatility, 0)

    def test_invalid_inputs(self):
        for rows in [[], snapshots([100, 0]), snapshots([float("nan")]),
                     snapshots([100, 110])[::-1]]:
            with self.assertRaises(ValueError):
                summarize_performance(rows, 100)
        for kwargs in [{"initial_cash": 0}, {"periods_per_year": True}]:
            with self.assertRaises(ValueError):
                summarize_performance(snapshots([100]), **kwargs)
