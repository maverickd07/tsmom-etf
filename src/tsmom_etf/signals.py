"""Momentum directions lagged by one observation to avoid look-ahead."""

from collections import deque
from dataclasses import dataclass
from datetime import date
import math
from typing import Iterable, List, Optional

from .data import PriceObservation


@dataclass(frozen=True)
class MomentumSignal:
    date: date
    symbol: str
    direction: Optional[int]


def lagged_momentum(
    observations: Iterable[PriceObservation], lookback: int
) -> List[MomentumSignal]:
    """Return directions for each observation using only earlier closes.

    For symbol observation i, compare price[i-1] with price[i-1-lookback].
    Direction is +1, -1, or 0; insufficient history produces None. Lookback
    counts observed intervals, not calendar days. No missing prices are filled.
    """
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 1:
        raise ValueError("lookback must be a positive integer")
    histories = {}
    last_dates = {}
    signals = []
    for observation in observations:
        symbol = observation.symbol
        if not symbol or symbol != symbol.strip():
            raise ValueError("symbol must be nonempty without surrounding whitespace")
        if not math.isfinite(observation.adjusted_close) or observation.adjusted_close <= 0:
            raise ValueError("prices must be finite and positive")
        if symbol in last_dates and observation.date <= last_dates[symbol]:
            raise ValueError("dates must strictly increase within each symbol")
        history = histories.setdefault(symbol, deque(maxlen=lookback + 1))
        direction = None
        if len(history) == lookback + 1:
            direction = (history[-1] > history[0]) - (history[-1] < history[0])
        signals.append(MomentumSignal(observation.date, symbol, direction))
        history.append(observation.adjusted_close)
        last_dates[symbol] = observation.date
    return signals
