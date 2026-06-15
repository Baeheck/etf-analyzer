import pandas as pd


def run_backtest(prices: pd.DataFrame, ticker: str, amount: float, start_date: str) -> dict:
    """
    Simulates investing a lump sum on a given date and holding until today.

    Returns a dict with:
    - dates, portfolio_values: for plotting
    - invested, current_value, gain_loss, return_pct
    - best/worst day
    """
    if ticker not in prices.columns:
        return None

    series = prices[ticker].dropna()

    # Find the closest available trading date on or after start_date
    target = pd.Timestamp(start_date)
    available = series.index[series.index >= target]
    if available.empty:
        return {"error": f"No data available from {start_date}. Try a later date."}

    actual_start = available[0]
    series = series[actual_start:]

    if len(series) < 2:
        return {"error": "Not enough data from that date. Try an earlier date."}

    buy_price = series.iloc[0]
    shares = amount / buy_price
    portfolio = series * shares

    daily_returns = series.pct_change().dropna()
    best_day = daily_returns.idxmax()
    worst_day = daily_returns.idxmin()

    current_value = portfolio.iloc[-1]
    gain_loss = current_value - amount
    return_pct = (current_value / amount - 1) * 100

    return {
        "ticker": ticker,
        "actual_start": actual_start.strftime("%Y-%m-%d"),
        "invested": amount,
        "current_value": round(current_value, 2),
        "gain_loss": round(gain_loss, 2),
        "return_pct": round(return_pct, 2),
        "dates": portfolio.index.tolist(),
        "portfolio_values": portfolio.round(2).tolist(),
        "best_day": {"date": best_day.strftime("%Y-%m-%d"), "pct": round(daily_returns[best_day] * 100, 2)},
        "worst_day": {"date": worst_day.strftime("%Y-%m-%d"), "pct": round(daily_returns[worst_day] * 100, 2)},
    }
