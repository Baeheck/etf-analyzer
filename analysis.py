import pandas as pd
import numpy as np

# Approximate trading days per period
PERIOD_DAYS = {"1M": 21, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260}


def compute_return(series: pd.Series, days: int) -> float | None:
    """Percentage return over the last N trading days."""
    series = series.dropna()
    if len(series) < days:
        return None
    return (series.iloc[-1] / series.iloc[-days] - 1) * 100


def compute_cagr(series: pd.Series, years: float) -> float | None:
    """Compound Annual Growth Rate over N years."""
    series = series.dropna()
    days = int(years * 252)
    if len(series) < days:
        return None
    return ((series.iloc[-1] / series.iloc[-days]) ** (1 / years) - 1) * 100


def compute_sharpe(series: pd.Series) -> float | None:
    """
    Annualized Sharpe ratio using the last year of data.
    Assumes risk-free rate = 0 (fair for comparison purposes).
    Higher = better risk-adjusted return.
    """
    series = series.dropna().tail(252)
    daily_returns = series.pct_change().dropna()
    if daily_returns.std() == 0 or len(daily_returns) < 20:
        return None
    return (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)


def compute_max_drawdown(series: pd.Series) -> float:
    """
    Largest peak-to-trough decline in the full history.
    E.g. -50% means the ETF lost half its value from its peak at some point.
    """
    series = series.dropna()
    rolling_max = series.cummax()
    drawdown = (series - rolling_max) / rolling_max * 100
    return drawdown.min()


def compute_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    """Build a summary metrics table for all ETFs."""
    rows = []
    for ticker in prices.columns:
        s = prices[ticker].dropna()
        row = {
            "ETF": ticker,
            "1M %": compute_return(s, 21),
            "6M %": compute_return(s, 126),
            "1Y %": compute_return(s, 252),
            "3Y CAGR %": compute_cagr(s, 3),
            "5Y CAGR %": compute_cagr(s, 5),
            "Sharpe (1Y)": compute_sharpe(s),
            "Max Drawdown %": compute_max_drawdown(s),
        }
        rows.append(row)

    return pd.DataFrame(rows).set_index("ETF")
