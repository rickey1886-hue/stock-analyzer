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


def get_news_items(query: str, limit: int = 5) -> list[dict]:
    if not query:
        return []
    safe_limit = max(1, min(5, int(limit)))
    rss_url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"
    )
    try:
        with urlopen(rss_url, timeout=8) as response:
            xml_bytes = response.read()
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []

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
                "タイトル": title,
                "配信元": source,
                "日付": pub_date,
                "リンク": link,
            }
        )
    return items
