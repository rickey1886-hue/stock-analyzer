"""News headline retrieval (Phase 2 step 1)."""

from __future__ import annotations

from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET


def _safe_text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return "データ未取得"
    text = node.text.strip()
    return text if text else "データ未取得"


def _build_query(query: str | None, ticker: str | None, company_name: str | None) -> str:
    query_parts = []
    for value in [query, ticker, company_name]:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            query_parts.append(text)
    return " ".join(query_parts).strip()


def get_news_items(
    query: str | None = None,
    limit: int = 5,
    ticker: str | None = None,
    company_name: str | None = None,
    include_status: bool = False,
) -> list[dict] | dict:
    merged_query = _build_query(query=query, ticker=ticker, company_name=company_name)
    if not merged_query:
        return {"status": "ニュースデータ未取得", "items": []} if include_status else []
    safe_limit = max(1, min(5, int(limit)))
    rss_url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(merged_query)}&hl=ja&gl=JP&ceid=JP:ja"
    )
    try:
        with urlopen(rss_url, timeout=8) as response:
            xml_bytes = response.read()
        root = ET.fromstring(xml_bytes)
    except Exception:
        return {"status": "ニュースデータ未取得", "items": []} if include_status else []

    items = []
    for item in root.findall("./channel/item")[:safe_limit]:
        title = _safe_text(item.find("title"))
        link = _safe_text(item.find("link"))
        source = _safe_text(item.find("source"))
        pub_date_text = _safe_text(item.find("pubDate"))
        if pub_date_text != "データ未取得":
            try:
                pub_date = parsedate_to_datetime(pub_date_text).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pub_date = pub_date_text
        else:
            pub_date = "データ未取得"
        items.append(
            {
                "title": title,
                "source": source,
                "published": pub_date,
                "link": link,
            }
        )
    if not items:
        return {"status": "ニュースデータ未取得", "items": []} if include_status else []
    return {"status": "ok", "items": items} if include_status else items
