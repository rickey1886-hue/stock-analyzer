"""Ticker utility helpers."""


def normalize_ticker(raw_ticker: str) -> str:
    """Normalize ticker input while preserving .T format for JP stocks."""
    if not raw_ticker:
        return ""
    ticker = raw_ticker.strip().upper()
    return ticker
