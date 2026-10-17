from datetime import date, timedelta
import unittest

from tsmom_etf.evaluation import evaluate_walk_forward
from tsmom_etf.strategy import run_momentum


def panel(values):
    return [(date(2024, 1, 1) + timedelta(days=i), {"A": v})
            for i, v in enumerate(values)]


class WalkForwardEvaluationTests(unittest.TestCase):
    def test_causal_selection_and_earlier_fold_invariance(self):
        values = [100, 110, 105, 115, 120, 110, 115, 105, 110, 120, 115, 125]
        first = evaluate_walk_forward(panel(values), [1, 2], 6, 3, 2, cost_bps=5)
        altered = evaluate_walk_forward(panel(values[:9] + [80, 70, 90]), [1, 2], 6, 3, 2, cost_bps=5)
        self.assertEqual(len(first), 2)
        self.assertEqual(first[0], altered[0])
        self.assertEqual(first[1].lookback, altered[1].lookback)
        self.assertEqual(first[0].cash.total_return, 0)
        self.assertGreater(first[0].buy_and_hold.total_cost, 0)

    def test_training_tie_uses_first_candidate(self):
        result = evaluate_walk_forward(panel([100] * 12), [2, 1], 6, 3, 2)
        self.assertEqual([fold.lookback for fold in result], [2, 2])
        self.assertEqual(result[0].strategy.total_return, 0)

    def test_test_starts_with_cash_and_no_training_trades(self):
        rows = panel([100, 110, 105, 115, 120, 110, 115, 105, 110])
        ledger = run_momentum(rows, 1, 2, trade_start=6)
        self.assertTrue(all(step.equity == 10000 and step.traded_notional == 0 for step in ledger[:6]))
        self.assertEqual(ledger[6].gross_pnl, 0)

    def test_invalid_candidates_and_short_training(self):
        for candidates, train in [([], 6), ([0], 6), ([5], 6), ([1], 2)]:
            with self.assertRaises(ValueError):
                evaluate_walk_forward(panel([100] * 12), candidates, train, 3, 2)
