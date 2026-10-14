"""Strict loading of daily adjusted ETF prices."""

import csv
from dataclasses import dataclass
from datetime import date
import math
from typing import TextIO, List


@dataclass(frozen=True)
class PriceObservation:
    date: date
    symbol: str
    adjusted_close: float


def load_prices(source: TextIO) -> List[PriceObservation]:
    """Read a CSV stream, rejecting invalid rows without filling missing dates.

    Raises ValueError with a line number for invalid data. Input order is
    preserved; each symbol must have strictly increasing observation dates.
    """
    reader = csv.DictReader(source)
    required = {"date", "symbol", "adjusted_close"}
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or not required.issubset(fields):
        raise ValueError("CSV requires unique date, symbol, adjusted_close columns")
    observations = []
    last_dates = {}
    for row in reader:
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("row has a different number of fields than header")
            raw_date = row["date"]
            day = date.fromisoformat(raw_date)
            if day.isoformat() != raw_date:
                raise ValueError("date must use YYYY-MM-DD")
            symbol = row["symbol"]
            if not symbol or symbol != symbol.strip():
                raise ValueError("symbol must be nonempty without surrounding whitespace")
            price = float(row["adjusted_close"])
            if not math.isfinite(price) or price <= 0:
                raise ValueError("adjusted_close must be finite and positive")
            if symbol in last_dates and day <= last_dates[symbol]:
                raise ValueError("duplicate or out-of-order date for " + symbol)
        except (ValueError, TypeError) as error:
            raise ValueError("line {}: {}".format(reader.line_num, error)) from error
        observations.append(PriceObservation(day, symbol, price))
        last_dates[symbol] = day
    if not observations:
        raise ValueError("CSV contains no price observations")
    return observations
