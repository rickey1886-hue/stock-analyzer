"""News data access using Google News RSS."""

from __future__ import annotations

from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

NEWS_STATUS_FETCHED = "取得済み"
NEWS_STATUS_UNAVAILABLE = "ニュースデータ未取得"
DEFAULT_NEWS_MESSAGE = ""
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def _safe_text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return "データ未取得"
    text = node.text.strip()
    return text if text else "データ未取得"


def _build_news_query(ticker: str, company_name: str | None = None) -> str:
    query_parts = []
    for value in (ticker, company_name):
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in query_parts:
            query_parts.append(text)
    return " ".join(query_parts).strip()


def _safe_max_items(max_items: int) -> int:
    try:
        count = int(max_items)
    except (TypeError, ValueError):
        count = 5
    return max(1, min(5, count))


def _format_published(pub_date_text: str) -> str:
    if pub_date_text == "データ未取得":
        return pub_date_text
    try:
        return parsedate_to_datetime(pub_date_text).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, IndexError, OverflowError):
        return pub_date_text or "データ未取得"


def _unavailable_response(message: str) -> dict:
    return {
        "status": NEWS_STATUS_UNAVAILABLE,
        "items": [],
        "message": message,
    }


def fetch_company_news(ticker: str, company_name: str | None = None, max_items: int = 5) -> dict:
    """Fetch recent company news headlines from Google News RSS without an API key.

    The function intentionally does not classify sentiment, calculate news scores,
    or affect any investment judgment. It only returns headline metadata.
    """
    query = _build_news_query(ticker=ticker, company_name=company_name)
    if not query:
        return _unavailable_response("検索キーワードが未指定です")

    limit = _safe_max_items(max_items)
    rss_url = f"{GOOGLE_NEWS_RSS_URL}?q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"
    request = Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urlopen(request, timeout=8) as response:
            xml_bytes = response.read()
        root = ET.fromstring(xml_bytes)
    except Exception as exc:
        return _unavailable_response(f"ニュースRSS取得または解析に失敗しました: {exc}")

    items = []
    for item in root.findall("./channel/item")[:limit]:
        pub_date_text = _safe_text(item.find("pubDate"))
        items.append(
            {
                "title": _safe_text(item.find("title")),
                "source": _safe_text(item.find("source")),
                "published": _format_published(pub_date_text),
                "link": _safe_text(item.find("link")),
            }
        )

    if not items:
        return _unavailable_response("ニュースデータが空です")

    return {
        "status": NEWS_STATUS_FETCHED,
        "items": items,
        "message": DEFAULT_NEWS_MESSAGE,
    }


def get_news_items(ticker: str, company_name: str | None = None, max_items: int = 5) -> list[dict]:
    """Return only news items for callers that do not need status metadata."""
    return fetch_company_news(ticker=ticker, company_name=company_name, max_items=max_items)["items"]
