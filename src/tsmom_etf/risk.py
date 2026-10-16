"""Lagged volatility scaling and portfolio gross-exposure limits."""

from collections import deque
import math
from statistics import stdev
from typing import Iterable, List, Mapping, Optional


def lagged_volatility_scale(
    returns: Iterable[float], window: int, target_vol: float = 0.10,
    max_exposure: float = 1.0, periods_per_year: int = 252,
) -> List[Optional[float]]:
    """Scale each interval using sample volatility of prior interval returns.

    Warmup outputs are None. A zero-volatility window produces zero exposure
    rather than unbounded leverage. Inputs must be synchronized, equally
    spaced simple returns; missing dates must be handled before calling.
    Target volatility is annualized. Outputs are unsigned multipliers, not
    orders; multiply by a previously known direction and enforce portfolio
    limits before converting to executable holdings.
    """
    if isinstance(window, bool) or not isinstance(window, int) or window < 2:
        raise ValueError("window must be an integer of at least two")
    if (isinstance(periods_per_year, bool) or not isinstance(periods_per_year, int)
            or periods_per_year <= 0):
        raise ValueError("periods_per_year must be a positive integer")
    if not math.isfinite(target_vol) or target_vol <= 0:
        raise ValueError("target_vol must be finite and positive")
    if not math.isfinite(max_exposure) or max_exposure < 0:
        raise ValueError("max_exposure must be finite and nonnegative")
    history = deque(maxlen=window)
    result = []
    for value in returns:
        if not math.isfinite(value) or value < -1:
            raise ValueError("simple returns must be finite and at least -1")
        scale = None
        if len(history) == window:
            volatility = stdev(history) * math.sqrt(periods_per_year)
            scale = min(max_exposure, target_vol / volatility) if volatility > 0 else 0.0
        result.append(scale)
        history.append(value)
    return result


def cap_gross_exposure(weights: Mapping[str, float], limit: float = 1.0) -> dict:
    """Proportionally shrink weights when sum(abs(weights)) exceeds limit."""
    if not math.isfinite(limit) or limit < 0:
        raise ValueError("limit must be finite and nonnegative")
    if any(not math.isfinite(w) for w in weights.values()):
        raise ValueError("weights must be finite")
    gross = sum(abs(w) for w in weights.values())
    if not math.isfinite(gross):
        raise ValueError("gross exposure overflow")
    factor = limit / gross if gross > limit else 1.0
    return {symbol: weight * factor for symbol, weight in weights.items()}
