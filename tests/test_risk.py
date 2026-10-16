import math
import unittest
from tsmom_etf.risk import cap_gross_exposure, lagged_volatility_scale


class RiskTests(unittest.TestCase):
    def test_sample_volatility_and_warmup(self):
        values = lagged_volatility_scale([-.01, .01, .50], 2, .10, 10, 1)
        self.assertEqual(values[:2], [None, None])
        self.assertAlmostEqual(values[2], .10 / math.sqrt(.0002))

    def test_current_and_future_returns_do_not_change_current_scale(self):
        first = lagged_volatility_scale([-.01, .01, .02, .04], 2)
        other = lagged_volatility_scale([-.01, .01, -.8, .9], 2)
        self.assertEqual(first[:3], other[:3])

    def test_rolling_window_cap_and_zero_variance(self):
        values = lagged_volatility_scale([.01, .01, -.01, .01], 2, max_exposure=.2)
        self.assertEqual(values, [None, None, 0.0, .2])
        self.assertEqual(lagged_volatility_scale([0, .1, 0], 2, max_exposure=0)[2], 0)

    def test_gross_cap_preserves_signs_and_proportions(self):
        self.assertEqual(cap_gross_exposure({"A": 2, "B": -1}, 1.5), {"A": 1, "B": -.5})
        self.assertEqual(cap_gross_exposure({"A": .2}), {"A": .2})
        self.assertEqual(cap_gross_exposure({}), {})
        self.assertEqual(cap_gross_exposure({"A": 1}, 0), {"A": 0})

    def test_invalid_parameters_and_returns(self):
        for kwargs in [{"window": 1}, {"window": True}, {"window": 2, "target_vol": 0},
                       {"window": 2, "max_exposure": -1}, {"window": 2, "periods_per_year": 0}]:
            with self.assertRaises(ValueError):
                lagged_volatility_scale([], **kwargs)
        for value in [float("nan"), float("inf"), -1.01]:
            with self.assertRaises(ValueError):
                lagged_volatility_scale([value], 2)
        for weights, limit in [({"A": float("nan")}, 1), ({}, -1), ({}, float("inf"))]:
            with self.assertRaises(ValueError):
                cap_gross_exposure(weights, limit)
