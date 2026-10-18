import importlib.util
import json
from pathlib import Path
import unittest


class ExampleTests(unittest.TestCase):
    def test_deterministic_multisymbol_report(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "synthetic_walk_forward.py"
        spec = importlib.util.spec_from_file_location("synthetic_example", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.build_report()
        self.assertEqual(report, module.build_report())
        self.assertEqual(len(report["folds"]), 3)
        self.assertEqual(set(report["fixed_lookback_sensitivity"]), {"5", "10", "20"})
        for fold in report["folds"]:
            self.assertLess(fold["train_end"], fold["test_start"])
            self.assertEqual(fold["cash"]["total_return"], 0)
        json.dumps(report, allow_nan=False)
