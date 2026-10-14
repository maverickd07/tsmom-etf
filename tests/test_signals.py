from datetime import date, timedelta
import unittest

from tsmom_etf.data import PriceObservation
from tsmom_etf.signals import lagged_momentum


def prices(values, symbol="SPY"):
    return [PriceObservation(date(2024, 1, 1) + timedelta(days=i), symbol, p)
            for i, p in enumerate(values)]


class MomentumTests(unittest.TestCase):
    def test_warmup_and_positive_negative_flat_directions(self):
        result = lagged_momentum(prices([100, 110, 100, 100, 90]), 1)
        self.assertEqual([s.direction for s in result], [None, None, 1, -1, 0])

    def test_lookback_counts_intervals(self):
        result = lagged_momentum(prices([100, 90, 110, 80]), 2)
        self.assertEqual([s.direction for s in result], [None, None, None, 1])

    def test_current_and_future_prices_cannot_change_signal(self):
        base = lagged_momentum(prices([100, 110, 120, 130]), 1)
        changed = lagged_momentum(prices([100, 110, 1, 999]), 1)
        self.assertEqual(base[:3], changed[:3])

    def test_symbol_histories_are_independent(self):
        a, b = prices([100, 110, 120]), prices([100, 90, 80], "TLT")
        rows = [row for pair in zip(a, b) for row in pair]
        self.assertEqual([s.direction for s in lagged_momentum(rows, 1)],
                         [None, None, None, None, 1, -1])

    def test_gaps_are_not_filled(self):
        rows = prices([100, 110, 120])
        rows[2] = PriceObservation(date(2024, 2, 1), "SPY", 120)
        result = lagged_momentum(rows, 1)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[-1].direction, 1)

    def test_invalid_lookbacks(self):
        for value in [0, -1, 1.5, True, "2"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                lagged_momentum([], value)

    def test_invalid_observations(self):
        for value in [0, -1, float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                lagged_momentum(prices([100, value]), 1)
        for rows in [prices([100]) * 2, list(reversed(prices([100, 110]))), prices([100], "")]:
            with self.assertRaises(ValueError):
                lagged_momentum(rows, 1)


if __name__ == "__main__":
    unittest.main()
