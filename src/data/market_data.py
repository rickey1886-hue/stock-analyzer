"""Market environment data access for Phase 2."""

from __future__ import annotations

import math
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
SYMBOL_FALLBACKS = {
    "^TOPX": ["998405.T"],
}


def _download_close_series(symbol: str, period: str) -> pd.Series | None:
    data = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
    if data is None or data.empty:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    if "Close" not in data.columns:
        return None
    close = data["Close"].dropna()
    close = close[close.apply(lambda v: math.isfinite(float(v)) if v is not None else False)]
    if close.empty:
        return None
    return close


def _download_close_with_fallback(symbol: str, period: str) -> tuple[pd.Series | None, str]:
    close = _download_close_series(symbol, period)
    if close is not None:
        return close, symbol
    for fallback_symbol in SYMBOL_FALLBACKS.get(symbol, []):
        fallback_close = _download_close_series(fallback_symbol, period)
        if fallback_close is not None:
            return fallback_close, fallback_symbol
    return None, symbol


def _calc_return(close: pd.Series | None) -> float | None:
    if close is None or len(close) < 2:
        return None
    first = close.iloc[0]
    last = close.iloc[-1]
    if first in (None, 0):
        return None
    try:
        first_f = float(first)
        last_f = float(last)
        if not math.isfinite(first_f) or not math.isfinite(last_f) or first_f == 0:
            return None
        result = (last_f / first_f) - 1.0
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def get_market_environment(period: str) -> dict:
    market_rows = []
    market_returns = {}

    for name, symbol in MARKET_SYMBOLS:
        close, used_symbol = _download_close_with_fallback(symbol, period)
        latest = None
        if close is not None:
            try:
                latest_value = float(close.iloc[-1])
                latest = latest_value if math.isfinite(latest_value) else None
            except (TypeError, ValueError):
                latest = None
        change_rate = _calc_return(close)
        market_rows.append(
            {
                "指数": name,
                "シンボル": used_symbol,
                "終値": latest,
                "期間騰落率": change_rate,
            }
        )
        market_returns[name] = change_rate

    return {
        "market_rows": market_rows,
        "market_returns": market_returns,
    }
