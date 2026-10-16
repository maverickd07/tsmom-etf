"""Simple benchmarks using the same cash and cost ledger as strategies."""

from typing import Iterable, List

from .accounting import PortfolioStep, account_portfolio


def cash_benchmark(prices: Iterable[tuple], initial_cash: float = 10000.0) -> List[PortfolioStep]:
    """Hold initial cash without interest over the supplied price dates."""
    return account_portfolio(prices, {}, initial_cash=initial_cash)


def equal_weight_buy_and_hold(
    prices: Iterable[tuple], initial_cash: float = 10000.0, cost_bps: float = 0.0,
) -> List[PortfolioStep]:
    """Buy equal notional amounts at the first close, then hold fixed shares.

    Reserve proportional entry costs from initial cash so the portfolio does
    not borrow to pay fees. Later market moves cause weights to drift. No final
    liquidation is assumed; ending equity marks open holdings to market.
    Fractional synthetic adjusted-price shares are permitted.
    """
    rows = [(day, dict(panel)) for day, panel in prices]
    # Validate all rows and parameters before calculating any target quantities.
    account_portfolio(rows, {}, initial_cash=initial_cash, cost_bps=cost_bps)
    if not rows:
        return []
    day, first = rows[0]
    allocation = initial_cash / (1 + cost_bps / 10000.0) / len(first)
    shares = {symbol: allocation / price for symbol, price in first.items()}
    return account_portfolio(rows, {day: shares}, initial_cash, cost_bps)
