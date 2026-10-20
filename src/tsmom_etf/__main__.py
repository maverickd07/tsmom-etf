"""Generate a walk-forward JSON report from an adjusted-price CSV snapshot."""

import argparse
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import sys

from .data import load_prices
from .evaluation import evaluate_walk_forward


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prices", type=Path)
    parser.add_argument("--train-size", type=int, required=True)
    parser.add_argument("--test-size", type=int, required=True)
    parser.add_argument("--vol-window", type=int, default=20)
    parser.add_argument("--lookbacks", type=int, nargs="+", default=[21, 63, 126])
    parser.add_argument("--gap", type=int, default=0)
    parser.add_argument("--expanding", action="store_true")
    parser.add_argument("--initial-cash", type=float, default=10000)
    parser.add_argument("--cost-bps", type=float, default=5)
    parser.add_argument("--symbols", nargs="+", help="Expected complete symbol universe")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--adjustment", required=True)
    args = parser.parse_args(argv)
    try:
        if any(not value.strip() for value in (args.provider, args.currency, args.adjustment)):
            raise ValueError("provenance fields must be nonempty")
        snapshot = args.prices.read_bytes()
        observations = load_prices(io.StringIO(snapshot.decode("utf-8")))
        grouped = {}
        for observation in observations:
            grouped.setdefault(observation.date, {})[observation.symbol] = observation.adjusted_close
        panel = sorted(grouped.items())
        actual_symbols = {observation.symbol for observation in observations}
        if args.symbols is not None:
            expected = set(args.symbols)
            if (len(expected) != len(args.symbols)
                    or any(not symbol or symbol != symbol.strip() for symbol in expected)):
                raise ValueError("expected symbols must be unique and nonempty without surrounding whitespace")
            if actual_symbols != expected:
                missing = sorted(expected - actual_symbols)
                unexpected = sorted(actual_symbols - expected)
                raise ValueError("symbol universe mismatch: missing={}, unexpected={}".format(missing, unexpected))
        folds = evaluate_walk_forward(
            panel, args.lookbacks, args.train_size, args.test_size, args.vol_window,
            args.gap, args.expanding, args.initial_cash, args.cost_bps)
        if not folds:
            raise ValueError("not enough observations for a complete evaluation fold")
        output = []
        for fold in folds:
            output.append({
                "train_start": panel[fold.split.train.start][0].isoformat(),
                "train_end": panel[fold.split.train.stop - 1][0].isoformat(),
                "test_start": panel[fold.split.test.start][0].isoformat(),
                "test_end": panel[fold.split.test.stop - 1][0].isoformat(),
                "lookback": fold.lookback,
                "strategy": asdict(fold.strategy),
                "buy_and_hold": asdict(fold.buy_and_hold), "cash": asdict(fold.cash)})
        report = {
            "input": {"sha256": hashlib.sha256(snapshot).hexdigest(),
                      "provider": args.provider, "currency": args.currency,
                      "adjustment": args.adjustment, "sessions": len(panel),
                      "symbols": sorted(panel[0][1])},
            "parameters": {key: value for key, value in vars(args).items()
                           if key not in ("prices", "provider", "currency", "adjustment")},
            "assumptions": {"annualization": 252, "capital": "fixed initial capital",
                            "execution": "prior-close sizing, next-close fill",
                            "folds": "independent cash resets",
                            "calendar": "caller must verify equally spaced sessions"},
            "folds": output}
        payload = json.dumps(report, indent=2, allow_nan=False)
    except (OSError, UnicodeError, ValueError, OverflowError) as error:
        parser.error(str(error))
    sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
