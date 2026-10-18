"""Cash and holdings accounting on a synchronized adjusted-price panel."""

from dataclasses import dataclass
from datetime import date
import math
from typing import Iterable, Mapping, List


@dataclass(frozen=True)
class PortfolioStep:
    date: date
    gross_pnl: float
    traded_notional: float
    cost: float
    cash: float
    equity: float
    gross_market_value: float = 0.0
    net_market_value: float = 0.0


def account_portfolio(
    prices: Iterable[tuple],
    executed_holdings: Mapping[date, Mapping[str, float]],
    initial_cash: float = 10000.0,
    cost_bps: float = 0.0,
) -> List[PortfolioStep]:
    """Account for explicit target share holdings executed at each dated close.

    Each price row is (date, {symbol: adjusted_close}); every row must contain
    the same universe. Targets are complete share holdings, not weights, and
    omitted symbols in a target are liquidated. Without a target, holdings stay
    unchanged. Prior holdings earn the price move before close trades occur.
    The caller must supply executable targets known before their fill, not
    same-close signals. Shorting and negative cash are allowed; financing,
    borrow fees, and cash interest are not modeled. Adjusted shares are
    synthetic units, with distributions already included in adjusted prices.
    """
    if not math.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be finite and positive")
    if not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("cost_bps must be finite and nonnegative")
    cash = initial_cash
    holdings = {}
    previous = None
    last_day = None
    seen = set()
    results = []
    for day, raw_prices in prices:
        panel = dict(raw_prices)
        if last_day is not None and day <= last_day:
            raise ValueError("price dates must strictly increase")
        if not panel or any(not s or not isinstance(s, str) for s in panel):
            raise ValueError("price universe must contain nonempty symbols")
        if previous is not None and panel.keys() != previous.keys():
            raise ValueError("price universe must be identical on every date")
        if any(not math.isfinite(p) or p <= 0 for p in panel.values()):
            raise ValueError("prices must be finite and positive")
        gross = 0.0 if previous is None else sum(
            q * (panel[s] - previous[s]) for s, q in holdings.items())
        traded = 0.0
        if day in executed_holdings:
            target = dict(executed_holdings[day])
            if not target.keys() <= panel.keys():
                raise ValueError("target contains symbols without prices")
            if any(not math.isfinite(q) for q in target.values()):
                raise ValueError("holdings must be finite")
            for symbol in panel:
                delta = target.get(symbol, 0.0) - holdings.get(symbol, 0.0)
                notional = delta * panel[symbol]
                cash -= notional
                traded += abs(notional)
            holdings = target
        cost = traded * cost_bps / 10000.0
        cash -= cost
        net_value = sum(q * panel[s] for s, q in holdings.items())
        gross_value = sum(abs(q * panel[s]) for s, q in holdings.items())
        equity = cash + net_value
        if not all(math.isfinite(v) for v in (gross, traded, cost, cash, equity, gross_value, net_value)):
            raise ValueError("accounting overflow")
        results.append(PortfolioStep(day, gross, traded, cost, cash, equity, gross_value, net_value))
        previous, last_day = panel, day
        seen.add(day)
    if not executed_holdings.keys() <= seen:
        raise ValueError("execution dates must occur in the price panel")
    return results
