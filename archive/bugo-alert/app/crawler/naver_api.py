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

MAX_PAGES = 10
PER_PAGE = 100


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
    import re
    return re.sub(r"<[^>]+>", "", text)


async def _fetch_page(
    client: httpx.AsyncClient,
    headers: dict,
    query: str,
    start: int,
) -> list[NewsItem]:
    """단일 페이지를 가져온다."""
    params = {
        "query": query,
        "display": PER_PAGE,
        "start": start,
        "sort": "date",
    }
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
    return items


async def search_obituary_news(
    query: str = "부고",
    max_pages: int = MAX_PAGES,
) -> tuple[list[NewsItem], int]:
    """네이버 뉴스를 페이지네이션하여 최대 max_pages * 100건을 수집한다.

    네이버 API 제한: start는 1~1000, display는 최대 100.
    일일 25,000회 제한 → 1회 크롤링≈10호출 → 약 2,500회/일 가능.

    Returns:
        (items, api_calls): 수집된 뉴스 목록, API 호출 횟수
    """
    settings = get_settings()
    if not settings.naver_client_id or settings.naver_client_id == "your_naver_client_id":
        logger.warning("네이버 API 키 미설정 — 크롤링을 건너뜁니다")
        return [], 0

    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }

    all_items: list[NewsItem] = []
    seen_links: set[str] = set()
    api_calls = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(max_pages):
            start = page * PER_PAGE + 1
            if start > 1000:
                break

            try:
                items = await _fetch_page(client, headers, query, start)
                api_calls += 1
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning("네이버 API 페이지 %d 요청 실패: %s", page + 1, e)
                break

            if not items:
                break

            for item in items:
                link = item.original_link or item.naver_link
                if link not in seen_links:
                    seen_links.add(link)
                    all_items.append(item)

            logger.info(
                "네이버 뉴스 페이지 %d 수신 %d건 (누적 %d건)",
                page + 1, len(items), len(all_items),
            )

            if len(items) < PER_PAGE:
                break

    logger.info("네이버 뉴스 검색 총 %d건 수신, API %d회 (query=%s)", len(all_items), api_calls, query)
    return all_items, api_calls
