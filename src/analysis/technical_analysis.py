"""Technical indicator calculations."""

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["MA25"] = out["Close"].rolling(25).mean()
    out["MA75"] = out["Close"].rolling(75).mean()
    out["MA200"] = out["Close"].rolling(200).mean()
    out["RSI"] = RSIIndicator(close=out["Close"], window=14).rsi()

    macd = MACD(close=out["Close"], window_slow=26, window_fast=12, window_sign=9)
    out["MACD"] = macd.macd()
    out["MACD_SIGNAL"] = macd.macd_signal()
    out["MACD_HIST"] = macd.macd_diff()

    bb = BollingerBands(close=out["Close"], window=20, window_dev=2)
    out["BB_HIGH"] = bb.bollinger_hband()
    out["BB_MID"] = bb.bollinger_mavg()
    out["BB_LOW"] = bb.bollinger_lband()
    return out
