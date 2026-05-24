"""Fundamental data access using yfinance."""

import yfinance as yf


def _safe_get(d: dict, key: str):
    v = d.get(key)
    return v if v is not None else None


def get_fundamental_snapshot(ticker: str) -> dict:
    tk = yf.Ticker(ticker)
    info = tk.info or {}

    market_cap = _safe_get(info, "marketCap")
    per = _safe_get(info, "trailingPE")
    pbr = _safe_get(info, "priceToBook")
    psr = _safe_get(info, "priceToSalesTrailing12Months")
    dividend_yield = _safe_get(info, "dividendYield")
    eps = _safe_get(info, "trailingEps")

    financials = tk.financials
    cashflow = tk.cashflow

    revenue = net_income = operating_cf = free_cf = None
    if financials is not None and not financials.empty:
        revenue = financials.loc["Total Revenue"].iloc[0] if "Total Revenue" in financials.index else None
        net_income = financials.loc["Net Income"].iloc[0] if "Net Income" in financials.index else None
    if cashflow is not None and not cashflow.empty:
        operating_cf = cashflow.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cashflow.index else None
        free_cf = cashflow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cashflow.index else None

    return {
        "market_cap": market_cap,
        "per": per,
        "pbr": pbr,
        "psr": psr,
        "dividend_yield": dividend_yield,
        "eps": eps,
        "revenue": revenue,
        "net_income": net_income,
        "operating_cf": operating_cf,
        "free_cf": free_cf,
    }
