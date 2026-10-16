from datetime import date, timedelta
import unittest

from tsmom_etf.benchmarks import cash_benchmark, equal_weight_buy_and_hold

DAYS = [date(2024, 1, 1) + timedelta(days=i) for i in range(3)]


class BenchmarkTests(unittest.TestCase):
    def test_equal_weight_entry_then_weight_drift(self):
        rows = list(zip(DAYS, [{"A": 100, "B": 50}, {"A": 120, "B": 40},
                               {"A": 130, "B": 50}]))
        result = equal_weight_buy_and_hold(iter(rows), 1000)
        self.assertEqual([v.equity for v in result], [1000, 1000, 1150])
        self.assertEqual([v.traded_notional for v in result], [1000, 0, 0])
        self.assertEqual([v.gross_pnl for v in result], [0, 0, 150])

    def test_entry_cost_reserved_from_capital(self):
        rows = [(DAYS[0], {"A": 100}), (DAYS[1], {"A": 110})]
        result = equal_weight_buy_and_hold(rows, 1000, 100)
        self.assertAlmostEqual(result[0].cash, 0)
        self.assertAlmostEqual(result[0].traded_notional, 1000 / 1.01)
        self.assertAlmostEqual(result[0].cost, 1000 - 1000 / 1.01)
        self.assertAlmostEqual(result[1].equity, 1100 / 1.01)
        self.assertEqual(result[1].cost, 0)

    def test_cash_stays_flat(self):
        rows = [(DAYS[0], {"A": 100}), (DAYS[1], {"A": 50})]
        result = cash_benchmark(rows, 1000)
        self.assertEqual([v.equity for v in result], [1000, 1000])
        self.assertEqual([v.traded_notional for v in result], [0, 0])

    def test_empty_and_invalid_inputs(self):
        self.assertEqual(equal_weight_buy_and_hold([], 1000), [])
        for rows, cash, cost in [([(DAYS[0], {})], 1000, 0),
                                 ([(DAYS[0], {"A": 0})], 1000, 0),
                                 ([], 0, 0), ([], 1000, -1)]:
            with self.assertRaises(ValueError):
                equal_weight_buy_and_hold(rows, cash, cost)
