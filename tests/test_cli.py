import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tsmom_etf.__main__ import main


class CliTests(unittest.TestCase):
    def invoke(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            path.write_text(content)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main([str(path), "--train-size", "6", "--test-size", "3",
                      "--vol-window", "2", "--lookbacks", "1", "2",
                      "--provider", "synthetic", "--currency", "USD",
                      "--adjustment", "synthetic total return"])
            return json.loads(output.getvalue())

    def test_report_contains_digest_and_parameters(self):
        content = "date,symbol,adjusted_close\n" + "".join(
            "2024-01-{:02d},A,{}\n".format(i+1, 100+i+(i%2)) for i in range(12))
        report = self.invoke(content)
        self.assertEqual(report["input"]["sha256"], hashlib.sha256(content.encode()).hexdigest())
        self.assertEqual(report["input"]["symbols"], ["A"])
        self.assertEqual(len(report["folds"]), 2)
        self.assertEqual(report["parameters"]["lookbacks"], [1, 2])

    def test_invalid_input_and_insufficient_history_fail(self):
        for content in ["invalid", "date,symbol,adjusted_close\n2024-01-01,A,100\n"]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                self.invoke(content)
            self.assertEqual(error.exception.code, 2)
