"""Formatting helpers."""

from typing import Any
import math


def format_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "データ未取得"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "データ未取得"
    if not math.isfinite(numeric):
        return "データ未取得"
    return f"{numeric:,.{digits}f}"


def format_percent(value: Any, digits: int = 2) -> str:
    if value is None:
        return "データ未取得"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "データ未取得"
    if not math.isfinite(numeric):
        return "データ未取得"

    # yfinanceの配当利回りは 0.016 (比率) と 1.6 (既に%) の両方があり得るため、
    # 1以下は比率として100倍、1より大きい値は%値としてそのまま表示する。
    percent_value = numeric * 100 if abs(numeric) <= 1 else numeric
    return f"{percent_value:.{digits}f}%"
