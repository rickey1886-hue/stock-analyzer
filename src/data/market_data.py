"""Market environment data access for Phase 2."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

MARKET_SYMBOLS = [
    ("S&P500", "^GSPC"),
    ("NASDAQ", "^IXIC"),
    ("日経平均", "^N225"),
    ("TOPIX", "^TOPX"),
    ("SOX指数", "^SOX"),
    ("VIX指数", "^VIX"),
    ("ドル円", "JPY=X"),
    ("原油価格", "CL=F"),
]


def _download_close_series(symbol: str, period: str) -> pd.Series | None:
    data = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
    if data is None or data.empty:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    if "Close" not in data.columns:
        return None
    close = data["Close"].dropna()
    if close.empty:
        return None
    return close


def _calc_return(close: pd.Series | None) -> float | None:
    if close is None or len(close) < 2:
        return None
    first = close.iloc[0]
    last = close.iloc[-1]
    if first in (None, 0):
        return None
    try:
        return (float(last) / float(first)) - 1.0
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def get_market_environment(period: str) -> dict:
    market_rows = []
    market_returns = {}

    for name, symbol in MARKET_SYMBOLS:
        close = _download_close_series(symbol, period)
        latest = float(close.iloc[-1]) if close is not None else None
        change_rate = _calc_return(close)
        market_rows.append(
            {
                "指数": name,
                "シンボル": symbol,
                "終値": latest,
                "期間騰落率": change_rate,
            }
        )
        market_returns[name] = change_rate

    return {
        "market_rows": market_rows,
        "market_returns": market_returns,
    }
