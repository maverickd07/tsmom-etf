from datetime import date, timedelta
import unittest
from tsmom_etf.evaluation import walk_forward_splits


def dates(n):
    return [date(2024, 1, 1) + timedelta(days=i) for i in range(n)]


class WalkForwardTests(unittest.TestCase):
    def test_rolling_windows_and_partial_tail(self):
        splits = walk_forward_splits(dates(10), 3, 2)
        self.assertEqual([(s.train.start, s.train.stop, s.test.start, s.test.stop)
                          for s in splits], [(0, 3, 3, 5), (2, 5, 5, 7), (4, 7, 7, 9)])

    def test_expanding_training_and_gap(self):
        splits = walk_forward_splits(dates(10), 3, 2, gap=1, expanding=True)
        self.assertEqual([(s.train.start, s.train.stop, s.test.start, s.test.stop)
                          for s in splits], [(0, 3, 4, 6), (0, 5, 6, 8), (0, 7, 8, 10)])

    def test_no_train_test_leakage_or_repeated_test_rows(self):
        days = dates(30)
        tested = set()
        for split in walk_forward_splits(days, 5, 3, gap=2):
            train = set(range(*split.train.indices(len(days))))
            test = set(range(*split.test.indices(len(days))))
            self.assertFalse(train & test)
            self.assertFalse(tested & test)
            self.assertLess(max(train), min(test) - 1)
            tested.update(test)

    def test_insufficient_history(self):
        self.assertEqual(walk_forward_splits(dates(4), 3, 2), [])
        self.assertEqual(walk_forward_splits([], 3, 2), [])

    def test_invalid_sizes_and_dates(self):
        for kwargs in [{"train_size": 0, "test_size": 2},
                       {"train_size": 3, "test_size": True},
                       {"train_size": 3, "test_size": 2, "gap": -1},
                       {"train_size": 3, "test_size": 2, "expanding": 1}]:
            with self.assertRaises(ValueError):
                walk_forward_splits(dates(10), **kwargs)
        for days in [dates(2)[::-1], [date(2024, 1, 1)] * 2, ["2024-01-01"]]:
            with self.assertRaises(ValueError):
                walk_forward_splits(days, 1, 1)
