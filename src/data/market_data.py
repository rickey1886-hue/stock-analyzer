"""Market environment data helpers for Phase 2-1 / 2-2."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

INDEX_TICKERS = {
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "日経平均": "^N225",
    "TOPIX": "^TOPX",
    "SOX指数": "^SOX",
    "VIX指数": "^VIX",
    "ドル円": "JPY=X",
    "原油価格": "CL=F",
}


def _download_close_series(ticker: str, period: str) -> pd.Series:
    data = yf.download(ticker, period=period, interval="1d", auto_adjust=False, progress=False)
    if data is None or data.empty or "Close" not in data.columns:
        return pd.Series(dtype=float)
    close = data["Close"]
    return close.dropna()


def _calc_change_pct(close: pd.Series):
    if close is None or close.empty or len(close) < 2:
        return None
    first = close.iloc[0]
    last = close.iloc[-1]
    if first in (None, 0):
        return None
    try:
        return (float(last) / float(first)) - 1.0
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def get_market_indices(period: str) -> tuple[dict, list[str]]:
    rows = {}
    unavailable = []
    for name, ticker in INDEX_TICKERS.items():
        try:
            close = _download_close_series(ticker, period)
            if close.empty:
                rows[name] = {"ticker": ticker, "latest": None, "change_pct": None, "status": "データ未取得"}
                unavailable.append(name)
                continue
            rows[name] = {
                "ticker": ticker,
                "latest": float(close.iloc[-1]),
                "change_pct": _calc_change_pct(close),
                "status": "取得成功",
            }
        except Exception:
            rows[name] = {"ticker": ticker, "latest": None, "change_pct": None, "status": "データ未取得"}
            unavailable.append(name)
    return rows, unavailable


def infer_market_type(ticker: str) -> str:
    return "JP" if ticker.endswith(".T") else "US"


def compare_with_market(ticker: str, stock_price_df: pd.DataFrame, market_rows: dict) -> tuple[list[dict], str, dict]:
    stock_change = _calc_change_pct(stock_price_df["Close"].dropna()) if (stock_price_df is not None and not stock_price_df.empty and "Close" in stock_price_df.columns) else None
    market_type = infer_market_type(ticker)
    related = ["日経平均", "TOPIX"] if market_type == "JP" else ["S&P500", "NASDAQ"]
    if ticker.upper().startswith(("NVDA", "AMD", "TSM")) or ticker.upper().endswith(".T") and ticker.startswith(("8035", "6920", "6857", "9984")):
        related.append("SOX指数")

    comparisons = []
    outperform_count = 0
    valid_count = 0
    for name in related:
        row = market_rows.get(name, {})
        idx_change = row.get("change_pct")
        if stock_change is None or idx_change is None:
            comparisons.append({
                "比較対象": name,
                "個別株騰落率": stock_change,
                "指数騰落率": idx_change,
                "比較": "データ未取得",
                "コメント": "比較に必要なデータ未取得",
            })
            continue

        valid_count += 1
        if stock_change > idx_change:
            outperform_count += 1
            relation = "上回る"
            comment = "個別株が相対的に強い推移"
        elif stock_change < idx_change:
            relation = "下回る"
            comment = "指数対比でやや弱い推移"
        else:
            relation = "同程度"
            comment = "指数と同程度の推移"

        comparisons.append({
            "比較対象": name,
            "個別株騰落率": stock_change,
            "指数騰落率": idx_change,
            "比較": relation,
            "コメント": comment,
        })

    if valid_count == 0:
        env_comment = "市場比較データが不足しているため、相対評価はデータ未取得です。"
        market_score = {"score": None, "comment": "データ未取得"}
    else:
        env_comment = (
            "主要指数に対して概ね優位です。" if outperform_count >= (valid_count / 2)
            else "主要指数に対してやや劣後しています。"
        )
        market_score_val = int(50 + (outperform_count - (valid_count - outperform_count)) * 10)
        market_score = {"score": max(0, min(100, market_score_val)), "comment": "市場比較の補助スコア"}

    status = {
        "対象市場": "日本株" if market_type == "JP" else "米国株",
        "比較対象": "、".join(related),
        "取得状況": "比較可能" if valid_count > 0 else "データ未取得",
    }
    return comparisons, env_comment, market_score | status
