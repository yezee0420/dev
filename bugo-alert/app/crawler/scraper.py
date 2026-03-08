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

# dailyesports.com, gasnews.com 등 사이트별 추가 선택자
_SITE_SPECIFIC_SELECTORS = [
    ".view_content",
    "#articleBody",
    ".article-view",
    "#article-view-content-div",
    ".article_body",
    ".news_body_area",
    "#article_body",
    ".article-content",
]

# 부고 본문에 포함될 가능성이 높은 키워드 (검증·대체 전략용)
_OBITUARY_KEYWORDS = re.compile(
    r"별세|부친상|모친상|시부상|장인상|빙부상|빙모상|빈소|발인|장지|▲|△|◇|◆|▶"
)


def _has_obituary_content(text: str) -> bool:
    """텍스트에 부고 관련 키워드가 포함되어 있는지 확인한다."""
    return bool(text and _OBITUARY_KEYWORDS.search(text))


def _find_obituary_block(soup: BeautifulSoup) -> str | None:
    """부고 키워드를 포함하는 요소를 탐색하여 해당 블록 텍스트를 반환한다."""
    # string= 에 정규식 사용: NavigableString 중 키워드 포함 노드 탐색
    for pattern in ["별세", "부친상", "모친상", "빈소", "발인", "장지", "▲", "△"]:
        for node in soup.find_all(string=re.compile(re.escape(pattern))):
            parent = node.parent
            if parent and parent.name and parent.name not in ("script", "style", "nav"):
                # 직계 부모부터 시작해, 본문으로 보이는 가장 작은 블록 선택
                block = parent
                for _ in range(6):
                    if block and block.name:
                        text = block.get_text("\n", strip=True)
                        if 20 <= len(text) <= 2500 and _has_obituary_content(text):
                            return text  # 첫 매칭(가장 작은 블록) 반환
                        if len(text) > 2500:
                            break
                    block = block.parent if block else None
    return None


def _extract_body(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    all_selectors = _NAVER_ARTICLE_SELECTORS + _GENERIC_SELECTORS + _SITE_SPECIFIC_SELECTORS

    for sel in all_selectors:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 30:
            text = el.get_text("\n", strip=True)
            if _has_obituary_content(text):
                return text
            # 키워드 없어도 일단 후보로 보관 (다른 선택자에서 더 나은 결과 나올 수 있음)

    # 선택자로 추출했으나 키워드 없음 → 부고 블록 직접 탐색
    obit_block = _find_obituary_block(soup)
    if obit_block:
        return obit_block

    # 선택자 결과 중 가장 긴 것 사용 (키워드 검증 실패 시)
    best_text = ""
    for sel in all_selectors:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 30:
            t = el.get_text("\n", strip=True)
            if len(t) > len(best_text):
                best_text = t
    if best_text:
        return best_text

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
