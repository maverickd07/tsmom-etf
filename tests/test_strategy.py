from datetime import date, timedelta
import unittest

from tsmom_etf.strategy import run_momentum


def panel(values):
    return [(date(2024, 1, 1) + timedelta(days=i), {"A": v})
            for i, v in enumerate(values)]


class StrategyTests(unittest.TestCase):
    def run_strategy(self, values, **kwargs):
        return run_momentum(panel(values), 1, 2, initial_cash=1000,
                            target_vol=10, periods_per_year=1, **kwargs)

    def test_order_uses_previous_price_and_earns_only_after_fill(self):
        result = self.run_strategy([100, 110, 121, 100, 105, 110])
        # First two returns are identical: row 3 remains flat from zero variance.
        self.assertEqual([s.gross_pnl for s in result[:5]], [0, 0, 0, 0, 0])
        # Row 4 fills a short sized at row 3's price of 100.
        self.assertAlmostEqual(result[4].traded_notional, 1050)
        self.assertAlmostEqual(result[5].gross_pnl, -50)

    def test_future_changes_preserve_earlier_ledger(self):
        first = self.run_strategy([100, 110, 105, 115, 120, 110])
        changed = self.run_strategy([100, 110, 105, 115, 1, 900])
        self.assertEqual(first[:4], changed[:4])

    def test_current_price_does_not_change_order_quantity(self):
        first = self.run_strategy([100, 110, 105, 115])
        changed = self.run_strategy([100, 110, 105, 230])
        self.assertAlmostEqual(first[-1].traded_notional / 115,
                               changed[-1].traded_notional / 230)

    def test_costs_reduce_equity(self):
        values = [100, 110, 105, 115, 120]
        free = self.run_strategy(values)
        paid = self.run_strategy(values, cost_bps=10)
        self.assertAlmostEqual(free[-1].equity - paid[-1].equity,
                               sum(s.cost for s in paid))

    def test_empty_and_invalid_inputs(self):
        self.assertEqual(run_momentum([], 1, 2), [])
        with self.assertRaises(ValueError):
            run_momentum([], 0, 2)
        with self.assertRaises(ValueError):
            run_momentum(panel([100, 110]), 1, 2, gross_limit=-1)
