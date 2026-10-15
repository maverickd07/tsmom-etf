from datetime import date, timedelta
import unittest
from tsmom_etf.accounting import account_portfolio

DAYS = [date(2024, 1, 1) + timedelta(days=i) for i in range(3)]


class AccountingTests(unittest.TestCase):
    def test_buy_hold_and_liquidate_with_costs(self):
        rows = list(zip(DAYS, [{"SPY": 100}, {"SPY": 110}, {"SPY": 120}]))
        result = account_portfolio(rows, {DAYS[0]: {"SPY": 2}, DAYS[2]: {}}, 1000, 10)
        self.assertEqual([v.gross_pnl for v in result], [0, 20, 20])
        self.assertEqual([v.traded_notional for v in result], [200, 0, 240])
        self.assertAlmostEqual(result[-1].cost, .24)
        self.assertAlmostEqual(result[-1].cash, 1039.56)
        self.assertAlmostEqual(result[-1].equity, 1039.56)

    def test_close_trade_does_not_earn_previous_move(self):
        rows = list(zip(DAYS, [{"SPY": 100}, {"SPY": 200}, {"SPY": 210}]))
        result = account_portfolio(rows, {DAYS[1]: {"SPY": 1}}, 1000)
        self.assertEqual([v.gross_pnl for v in result], [0, 0, 10])
        self.assertEqual([v.equity for v in result], [1000, 1000, 1010])

    def test_multisymbol_short_and_reversal(self):
        rows = [(DAYS[0], {"A": 100, "B": 50}), (DAYS[1], {"A": 110, "B": 40})]
        targets = {DAYS[0]: {"A": 1, "B": -2}, DAYS[1]: {"A": -1, "B": 2}}
        result = account_portfolio(rows, targets, 1000)
        self.assertEqual(result[1].gross_pnl, 30)
        self.assertEqual(result[1].traded_notional, 380)
        self.assertEqual(result[1].equity, 1030)

    def test_repeated_target_does_not_trade(self):
        rows = [(d, {"A": 100 + i}) for i, d in enumerate(DAYS)]
        result = account_portfolio(rows, {d: {"A": 1} for d in DAYS})
        self.assertEqual([v.traded_notional for v in result], [100, 0, 0])

    def test_bad_panels_and_targets(self):
        cases = [([(DAYS[0], {"A": 0})], {}),
                 ([(DAYS[0], {"A": 1}), (DAYS[0], {"A": 1})], {}),
                 ([(DAYS[0], {"A": 1}), (DAYS[1], {"B": 1})], {}),
                 ([(DAYS[0], {"A": 1})], {DAYS[1]: {"A": 1}}),
                 ([(DAYS[0], {"A": 1})], {DAYS[0]: {"B": 1}}),
                 ([(DAYS[0], {"A": 1})], {DAYS[0]: {"A": float("nan")}})]
        for rows, targets in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                account_portfolio(rows, targets)

    def test_invalid_cash_and_cost(self):
        for cash, cost in [(0, 0), (float("nan"), 0), (1, -1), (1, float("inf"))]:
            with self.assertRaises(ValueError):
                account_portfolio([], {}, cash, cost)
