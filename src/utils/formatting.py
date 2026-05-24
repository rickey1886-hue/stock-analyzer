"""Formatting helpers."""

from typing import Any


def format_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "データ未取得"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "データ未取得"


def format_percent(value: Any, digits: int = 2) -> str:
    if value is None:
        return "データ未取得"
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "データ未取得"
