import io
import unittest
from datetime import date

from tsmom_etf.data import load_prices


class PriceLoadingTests(unittest.TestCase):
    def load(self, rows):
        return load_prices(io.StringIO("date,symbol,adjusted_close\n" + rows))

    def test_interleaved_symbols_and_gaps_preserve_input(self):
        values = self.load("2024-01-02,SPY,100\n2024-01-02,TLT,90\n2024-01-05,SPY,102\n")
        self.assertEqual(len(values), 3)
        self.assertEqual(values[2].date, date(2024, 1, 5))
        self.assertEqual(values[2].adjusted_close, 102)
        self.assertEqual([v.symbol for v in values], ["SPY", "TLT", "SPY"])

    def test_invalid_prices(self):
        for price in ["0", "-1", "nan", "inf", "-inf", "", "abc"]:
            with self.subTest(price=price), self.assertRaisesRegex(ValueError, "line 2"):
                self.load("2024-01-02,SPY," + price + "\n")

    def test_duplicate_and_reversed_dates(self):
        for day in ["2024-01-02", "2024-01-01"]:
            with self.subTest(day=day), self.assertRaisesRegex(ValueError, "line 3"):
                self.load("2024-01-02,SPY,100\n" + day + ",SPY,101\n")

    def test_invalid_dates_symbols_and_field_counts(self):
        for row in ["2024-02-30,SPY,100", "2024-1-2,SPY,100", "2024-01-02,,100",
                    "2024-01-02, SPY,100", "2024-01-02,SPY", "2024-01-02,SPY,100,extra"]:
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "line 2"):
                self.load(row + "\n")

    def test_missing_duplicate_headers_and_empty_data(self):
        for content in ["", "date,symbol,adjusted_close\n", "date,symbol\n",
                        "date,symbol,adjusted_close,symbol\n"]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                load_prices(io.StringIO(content))


if __name__ == "__main__":
    unittest.main()
