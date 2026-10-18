from datetime import date, timedelta
import unittest

from tsmom_etf.accounting import account_portfolio
from tsmom_etf.diagnostics import summarize_performance


class ExposureTests(unittest.TestCase):
    def test_long_short_values_and_post_cost_exposure(self):
        day = date(2024, 1, 1)
        ledger = account_portfolio([(day, {"A": 100, "B": 50})],
                                   {day: {"A": 2, "B": -1}}, 1000, 100)
        self.assertEqual(ledger[0].gross_market_value, 250)
        self.assertEqual(ledger[0].net_market_value, 150)
        summary = summarize_performance(ledger, 1000)
        self.assertAlmostEqual(summary.max_gross_exposure, 250 / 997.5)
        self.assertAlmostEqual(summary.mean_net_exposure, 150 / 997.5)

    def test_price_drift_and_liquidation(self):
        days = [date(2024, 1, 1) + timedelta(days=i) for i in range(3)]
        ledger = account_portfolio(list(zip(days, [{"A": 100}, {"A": 120}, {"A": 130}])),
                                   {days[0]: {"A": 2}, days[2]: {}}, 1000)
        self.assertEqual([s.gross_market_value for s in ledger], [200, 240, 0])
        summary = summarize_performance(ledger, 1000)
        self.assertAlmostEqual(summary.max_gross_exposure, 240 / 1040)
        self.assertAlmostEqual(summary.mean_gross_exposure, (.2 + 240 / 1040) / 3)
