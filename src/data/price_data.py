"""Price data access."""

import pandas as pd
import yfinance as yf


def get_price_history(ticker: str, period: str) -> pd.DataFrame:
    data = yf.download(ticker, period=period, interval="1d", auto_adjust=False, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def get_latest_price_stats(price_df: pd.DataFrame) -> dict:
    if price_df.empty:
        return {"latest_close": None, "recent_high": None, "recent_low": None}
    return {
        "latest_close": float(price_df["Close"].iloc[-1]),
        "recent_high": float(price_df["High"].max()),
        "recent_low": float(price_df["Low"].min()),
    }
