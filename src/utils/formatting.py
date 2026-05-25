"""Formatting helpers."""

import math
from typing import Any


def is_valid_number(value: Any, *, allow_zero: bool = True) -> bool:
    if value is None:
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(numeric):
        return False
    if not allow_zero and numeric == 0:
        return False
    return True


def format_number(value: Any, digits: int = 2) -> str:
    if not is_valid_number(value):
        return "データ未取得"
    return f"{float(value):,.{digits}f}"


def format_percent(value: Any, digits: int = 2) -> str:
    if not is_valid_number(value):
        return "データ未取得"
    numeric = float(value)

    # yfinanceの配当利回りは 0.016 (比率) と 1.6 (既に%) の両方があり得るため、
    # 1以下は比率として100倍、1より大きい値は%値としてそのまま表示する。
    percent_value = numeric * 100 if abs(numeric) <= 1 else numeric
    return f"{percent_value:.{digits}f}%"
