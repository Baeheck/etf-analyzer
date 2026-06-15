import yfinance as yf
import pandas as pd

# UCITS ETFs — available to European/Swiss retail investors.
# .L = London Stock Exchange (GBP). .DE = Xetra Germany (EUR).
ETFS = {
    "VWCE.DE": "Vanguard FTSE All-World (Acc, EUR) ★ recommended",
    "VWRL.L": "Vanguard FTSE All-World (Dist, GBP)",
    "IWDA.L": "iShares MSCI World — developed markets only (GBP)",
    "WSML.L": "iShares MSCI World Small Cap (GBP)",
    "EIMI.L": "iShares MSCI Emerging Markets IMI (GBP)",
    "IGLN.L": "iShares Physical Gold (GBP)",
    "BTCE.DE": "ETC Group Bitcoin ETP (EUR)",
}

# US-listed ETFs — NOT available to European retail investors (MiFID II / PRIIPs).
# Kept here for reference/comparison only.
ETFS_US_ONLY = {
    "AVGE": "Avantis All Equity Markets (US only)",
    "VT": "Vanguard Total World (US only)",
    "GLD": "SPDR Gold Shares (US only)",
    "IBIT": "iShares Bitcoin Trust (US only)",
}

def fetch_prices(tickers: list[str], period: str = "5y") -> pd.DataFrame:
    """
    Download adjusted closing prices for a list of tickers.
    Returns a DataFrame where each column is one ETF.
    period: "1mo", "6mo", "1y", "3y", "5y"
    """
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)

    # yfinance returns multi-level columns when >1 ticker; grab just "Close"
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})

    prices.dropna(how="all", inplace=True)
    return prices
