"""기사 원문 URL에 접속하여 본문 텍스트를 추출한다."""

from __future__ import annotations

import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

_NAVER_ARTICLE_SELECTORS = [
    "#dic_area",
    "#articeBody",
    "#newsct_article",
    ".article_body",
    "#articleBodyContents",
]

_GENERIC_SELECTORS = [
    "article",
    '[itemprop="articleBody"]',
    ".article-body",
    ".news_body",
    ".view_article",
    "#article-view-content-div",
    ".article_view",
    "#news_body_area",
]


def _extract_body(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for sel in _NAVER_ARTICLE_SELECTORS + _GENERIC_SELECTORS:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 30:
            return el.get_text("\n", strip=True)

    # fallback: 가장 긴 <p> 블록 집합 사용
    paragraphs = soup.find_all("p")
    if paragraphs:
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)
        if len(text) > 50:
            return text

    return soup.get_text("\n", strip=True)[:3000]


async def fetch_article_text(url: str) -> str:
    """URL에서 기사 본문 텍스트를 추출해 반환한다."""
    try:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return _extract_body(resp.text)
    except Exception as exc:
        logger.warning("기사 스크래핑 실패 url=%s error=%s", url, exc)
        return ""
