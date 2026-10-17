"""Performance summaries from a dated cash-and-holdings ledger."""

from dataclasses import dataclass
import math
from statistics import stdev
from typing import Iterable, Optional

from .accounting import PortfolioStep


@dataclass(frozen=True)
class PerformanceSummary:
    total_return: float
    max_drawdown: float
    annualized_volatility: Optional[float]
    total_cost: float
    traded_notional: float
    turnover_on_initial_capital: float


def summarize_performance(
    steps: Iterable[PortfolioStep], initial_cash: float = 10000.0,
    periods_per_year: int = 252,
) -> PerformanceSummary:
    """Summarize net equity, including entry costs against initial cash.

    Drawdown is a nonpositive fraction from the running equity peak, including
    initial capital. Volatility uses sample deviation of close-to-close simple
    returns, excluding the first snapshot (entry fees have no elapsed return
    interval). Fewer than two intervals yields None. Annualization assumes
    equally spaced sessions. Nonpositive equity is rejected rather than
    silently reporting ordinary return statistics after insolvency.
    """
    if not math.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be finite and positive")
    if (isinstance(periods_per_year, bool) or not isinstance(periods_per_year, int)
            or periods_per_year <= 0):
        raise ValueError("periods_per_year must be a positive integer")
    rows = list(steps)
    if not rows:
        raise ValueError("at least one ledger snapshot is required")
    peak = initial_cash
    drawdown = 0.0
    previous = None
    returns = []
    costs, traded = [], []
    for row in rows:
        if previous is not None and row.date <= previous.date:
            raise ValueError("snapshot dates must strictly increase")
        if not math.isfinite(row.equity) or row.equity <= 0:
            raise ValueError("equity must be finite and positive")
        if any(not math.isfinite(v) or v < 0 for v in (row.cost, row.traded_notional)):
            raise ValueError("costs and traded notional must be finite and nonnegative")
        peak = max(peak, row.equity)
        drawdown = min(drawdown, row.equity / peak - 1)
        if previous is not None:
            returns.append(row.equity / previous.equity - 1)
        costs.append(row.cost)
        traded.append(row.traded_notional)
        previous = row
    total_cost, total_traded = math.fsum(costs), math.fsum(traded)
    volatility = stdev(returns) * math.sqrt(periods_per_year) if len(returns) >= 2 else None
    total_return = rows[-1].equity / initial_cash - 1
    turnover = total_traded / initial_cash
    if any(not math.isfinite(v) for v in (total_return, total_cost, total_traded, turnover)):
        raise ValueError("performance arithmetic overflow")
    if volatility is not None and not math.isfinite(volatility):
        raise ValueError("volatility arithmetic overflow")
    return PerformanceSummary(total_return, drawdown, volatility,
                              total_cost, total_traded, turnover)
