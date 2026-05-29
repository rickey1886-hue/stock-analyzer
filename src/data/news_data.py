"""Google News RSS headline retrieval utilities."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests

NEWS_STATUS_FETCHED = "取得済み"
NEWS_STATUS_UNAVAILABLE = "ニュースデータ未取得"
MISSING_VALUE = "データ未取得"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
DEFAULT_MAX_ITEMS = 5
MAX_ITEMS_LIMIT = 5
REQUEST_TIMEOUT_SECONDS = 8


def _failure(message: str) -> dict:
    """Return the common failure shape expected by the application."""

    return {
        "status": NEWS_STATUS_UNAVAILABLE,
        "items": [],
        "message": message,
    }


def _safe_text(element: ET.Element | None) -> str:
    """Extract stripped text from an RSS element with a safe fallback."""

    if element is None or element.text is None:
        return MISSING_VALUE

    text = element.text.strip()
    return text if text else MISSING_VALUE


def _normalize_query_text(text: str) -> str:
    """Normalize the search term used for Google News RSS."""

    normalized = text.strip()
    if normalized.upper().endswith(".T"):
        normalized = normalized[:-2].strip()
    return normalized


def _build_search_query(ticker: str, company_name: str | None) -> str:
    """Build a search query, preferring company name over ticker."""

    preferred_query = company_name if company_name and company_name.strip() else ticker
    return _normalize_query_text(str(preferred_query)) if preferred_query is not None else ""


def _normalize_max_items(max_items: int) -> int:
    """Keep the requested item count within the supported Google News display range."""

    try:
        requested_items = int(max_items)
    except (TypeError, ValueError):
        requested_items = DEFAULT_MAX_ITEMS

    return max(1, min(requested_items, MAX_ITEMS_LIMIT))


def _parse_news_item(item: ET.Element) -> dict[str, str]:
    """Convert an RSS item element into the public news item dictionary."""

    return {
        "title": _safe_text(item.find("title")),
        "source": _safe_text(item.find("source")),
        "published": _safe_text(item.find("pubDate")),
        "link": _safe_text(item.find("link")),
    }


def fetch_company_news(
    ticker: str,
    company_name: str | None = None,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, Any]:
    """Fetch up to five company news headlines from Google News RSS.

    The function intentionally retrieves only RSS metadata (headline, source,
    published date, and link). It never fetches article bodies, and all expected
    network or parsing failures are converted into a safe response dictionary so
    callers do not need to wrap this function to keep the app running.
    """

    query = _build_search_query(ticker=ticker, company_name=company_name)
    if not query:
        return _failure("検索語が空のためニュースを取得できませんでした。")

    item_limit = _normalize_max_items(max_items)
    rss_url = (
        f"{GOOGLE_NEWS_RSS_URL}?"
        f"q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"
    )

    try:
        response = requests.get(rss_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return _failure("ニュース取得がタイムアウトしました。")
    except requests.exceptions.RequestException as exc:
        return _failure(f"ニュース取得中にネットワークエラーが発生しました: {exc}")

    if not response.content:
        return _failure("ニュースRSSのレスポンスが空でした。")

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        return _failure(f"ニュースRSSの解析に失敗しました: {exc}")

    channel = root.find("channel")
    if channel is None:
        return _failure("ニュースRSSの形式が想定と異なります。")

    rss_items = channel.findall("item")
    if not rss_items:
        return _failure("ニュースが見つかりませんでした。")

    items = [_parse_news_item(item) for item in rss_items[:item_limit]]
    if not items:
        return _failure("ニュースが見つかりませんでした。")

    return {
        "status": NEWS_STATUS_FETCHED,
        "items": items,
        "message": "",
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_company_news("AAPL", "Apple Inc.", 5))
