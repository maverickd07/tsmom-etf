"""Fixed-capital momentum strategy with orders sized before their fill."""

from typing import Iterable, List

from .accounting import PortfolioStep, account_portfolio
from .data import PriceObservation
from .risk import cap_gross_exposure, lagged_volatility_scale
from .signals import lagged_momentum


def run_momentum(
    prices: Iterable[tuple], lookback: int, vol_window: int,
    initial_cash: float = 10000.0, cost_bps: float = 0.0,
    target_vol: float = 0.10, max_asset_exposure: float = 1.0,
    gross_limit: float = 1.0, periods_per_year: int = 252,
    trade_start: int = 0,
) -> List[PortfolioStep]:
    """Size share orders from prior closes, execute at the next close.

    At row i, lagged direction and volatility use information through i-1.
    Desired fixed-capital weights are converted to shares using prices at i-1,
    then filled at close i. They first earn the move from i to i+1. Price moves
    before execution can make actual exposure exceed the sizing limits; these
    are order-sizing limits, not guaranteed post-fill exposure bounds.
    trade_start suppresses trading before that row while retaining feature history.
    Capital is fixed at initial_cash, not reinvested equity. No final
    liquidation is assumed. Price rows must be synchronized and equally spaced.
    """
    if isinstance(trade_start, bool) or not isinstance(trade_start, int) or trade_start < 0:
        raise ValueError("trade_start must be a nonnegative row index")
    rows = [(day, dict(panel)) for day, panel in prices]
    account_portfolio(rows, {}, initial_cash, cost_bps)
    # Validate parameters even for an empty input.
    lagged_momentum([], lookback)
    lagged_volatility_scale([], vol_window, target_vol, max_asset_exposure, periods_per_year)
    cap_gross_exposure({}, gross_limit)
    if not rows:
        return []
    directions, scales = {}, {}
    for symbol in rows[0][1]:
        observations = [PriceObservation(day, symbol, panel[symbol]) for day, panel in rows]
        directions[symbol] = lagged_momentum(observations, lookback)
        values = [panel[symbol] for _, panel in rows]
        # Return at row zero is unavailable, not a synthetic zero return.
        returns = [b / a - 1 for a, b in zip(values, values[1:])]
        scales[symbol] = [None] + lagged_volatility_scale(
            returns, vol_window, target_vol, max_asset_exposure, periods_per_year)
    targets = {}
    for i in range(max(1, trade_start), len(rows)):
        weights = {}
        for symbol in directions:
            direction = directions[symbol][i].direction
            scale = scales[symbol][i]
            weights[symbol] = 0.0 if direction is None or scale is None else direction * scale
        weights = cap_gross_exposure(weights, gross_limit)
        targets[rows[i][0]] = {
            symbol: initial_cash * weight / rows[i-1][1][symbol]
            for symbol, weight in weights.items()}
    return account_portfolio(rows, targets, initial_cash, cost_bps)
