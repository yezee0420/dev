"""네이버 뉴스 검색 API를 통해 부고 기사 목록을 조회한다."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"


@dataclass
class NewsItem:
    title: str
    original_link: str
    naver_link: str
    description: str
    pub_date: Optional[datetime]


def _parse_pub_date(raw: str) -> Optional[datetime]:
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        return None


def _strip_html(text: str) -> str:
    """<b>, </b> 등 간단한 HTML 태그를 제거한다."""
    import re
    return re.sub(r"<[^>]+>", "", text)


async def search_obituary_news(
    query: str = "부고",
    display: int = 100,
    start: int = 1,
    sort: str = "date",
) -> list[NewsItem]:
    settings = get_settings()
    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    items: list[NewsItem] = []
    for raw in data.get("items", []):
        items.append(
            NewsItem(
                title=_strip_html(raw.get("title", "")),
                original_link=raw.get("originallink", ""),
                naver_link=raw.get("link", ""),
                description=_strip_html(raw.get("description", "")),
                pub_date=_parse_pub_date(raw.get("pubDate", "")),
            )
        )

    logger.info("네이버 뉴스 검색 결과 %d건 수신 (query=%s)", len(items), query)
    return items
