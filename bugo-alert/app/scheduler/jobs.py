"""매시간 실행되는 크롤링 작업 + 즐겨찾기 매칭 알림."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Obituary, Favorite, NotificationLog
from app.crawler.naver_api import search_obituary_news
from app.crawler.scraper import fetch_article_text
from app.crawler.parser import parse_obituary, parse_obituary_multi, make_dedup_key, ParsedObituary
from app.notifications.email_sender import EmailNotifier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL 캐시: 이미 스크래핑한 URL을 건너뛰기 위한 LRU 캐시
# ---------------------------------------------------------------------------

from collections import OrderedDict

_URL_CACHE_MAX = 50_000


class _URLCache:
    """최대 크기를 가진 URL 캐시. 오래된 항목은 자동 제거."""

    def __init__(self, maxsize: int = _URL_CACHE_MAX):
        self._data: OrderedDict[str, None] = OrderedDict()
        self._maxsize = maxsize
        self._loaded = False

    def load_from_db(self, db: Session) -> None:
        if self._loaded:
            return
        rows = db.query(Obituary.source_url).all()
        for (url,) in rows:
            if url:
                self._data[url] = None
        self._loaded = True
        logger.info("기존 URL %d건 캐시 로드 완료", len(self._data))

    def __contains__(self, url: str) -> bool:
        return url in self._data

    def add(self, url: str) -> None:
        self._data[url] = None
        if len(self._data) > self._maxsize:
            self._data.popitem(last=False)


_seen_urls = _URLCache()


# ---------------------------------------------------------------------------
# 저장 / 매칭
# ---------------------------------------------------------------------------

_MERGE_FIELDS = (
    "deceased_name", "deceased_age", "funeral_hall", "room_number",
    "funeral_date", "funeral_time", "contact", "related_persons",
)

_SOFT_MATCH_WINDOW_DAYS = 7


def _find_existing(db: Session, dedup_key: str) -> Obituary | None:
    if not dedup_key:
        return None
    return db.query(Obituary).filter(Obituary.dedup_key == dedup_key).first()


def _find_soft_match(db: Session, parsed: ParsedObituary) -> Obituary | None:
    """dedup_key 정확 매칭 실패 시 소프트 매칭으로 기존 레코드를 찾는다."""
    cutoff = datetime.utcnow() - timedelta(days=_SOFT_MATCH_WINDOW_DAYS)

    if parsed.key_person and parsed.relationship:
        match = (
            db.query(Obituary)
            .filter(
                Obituary.key_person == parsed.key_person,
                Obituary.relationship == parsed.relationship,
                Obituary.created_at >= cutoff,
            )
            .first()
        )
        if match:
            return match

    if parsed.funeral_hall and parsed.key_person:
        match = (
            db.query(Obituary)
            .filter(
                Obituary.funeral_hall == parsed.funeral_hall,
                Obituary.key_person == parsed.key_person,
                Obituary.created_at >= cutoff,
            )
            .first()
        )
        if match:
            return match

    return None


def _fill_blank_fields(existing: Obituary, parsed: ParsedObituary) -> bool:
    """기존 레코드의 빈 필드를 새 파싱 결과로 보충한다."""
    updated = False
    for fld in _MERGE_FIELDS:
        old_val = getattr(existing, fld)
        new_val = getattr(parsed, fld, None)
        if not old_val and new_val:
            setattr(existing, fld, new_val)
            updated = True
    return updated


def _merge_and_save(db: Session, parsed: ParsedObituary, title: str, url: str,
                     raw_text: str, pub_date: datetime | None) -> tuple[Obituary | None, bool]:
    """기존 레코드가 있으면 빈 필드를 보충하고, 없으면 새로 생성한다.

    1차: dedup_key 정확 매칭
    2차: 소프트 매칭 (key_person+relationship 또는 key_person+funeral_hall)
    """
    dedup_key = make_dedup_key(parsed)

    existing = _find_existing(db, dedup_key)
    if not existing:
        existing = _find_soft_match(db, parsed)
        if existing:
            logger.debug("소프트 매칭 성공: id=%d, key_person=%s",
                         existing.id, existing.key_person)

    if existing:
        updated = _fill_blank_fields(existing, parsed)
        if not existing.dedup_key and dedup_key:
            existing.dedup_key = dedup_key
            updated = True
        if updated:
            db.commit()
            db.refresh(existing)
        return existing, False

    obit = Obituary(
        source_url=url,
        title=title,
        key_person=parsed.key_person,
        organization=parsed.organization,
        position=parsed.position,
        deceased_name=parsed.deceased_name,
        deceased_age=parsed.deceased_age,
        relationship=parsed.relationship,
        related_persons=parsed.related_persons,
        funeral_hall=parsed.funeral_hall,
        room_number=parsed.room_number,
        funeral_date=parsed.funeral_date,
        funeral_time=parsed.funeral_time,
        contact=parsed.contact,
        raw_text=raw_text[:5000] if raw_text else None,
        published_at=pub_date,
        dedup_key=dedup_key,
    )
    db.add(obit)
    try:
        db.commit()
        db.refresh(obit)
        return obit, True
    except IntegrityError:
        db.rollback()
        return None, False


def _match_favorites(db: Session, obit: Obituary) -> list[Favorite]:
    """부고 정보와 즐겨찾기 키워드를 매칭한다."""
    favorites = db.query(Favorite).filter(Favorite.is_active == True).all()
    if not favorites:
        return []

    searchable = " ".join(filter(None, [
        obit.key_person, obit.organization, obit.position,
        obit.deceased_name, obit.funeral_hall, obit.title,
        obit.related_persons, obit.raw_text,
    ]))

    keyword_matched = [f for f in favorites if f.keyword and f.keyword in searchable]
    if not keyword_matched:
        return []

    already_sent_ids = {
        row[0]
        for row in db.query(NotificationLog.favorite_id)
        .filter(
            NotificationLog.obituary_id == obit.id,
            NotificationLog.favorite_id.in_([f.id for f in keyword_matched]),
        )
        .all()
    }

    return [f for f in keyword_matched if f.id not in already_sent_ids]


async def _send_notifications(db: Session, obit: Obituary, favorites: list[Favorite]):
    notifier = EmailNotifier()
    for fav in favorites:
        success = await notifier.send(obit, fav)
        log = NotificationLog(
            obituary_id=obit.id,
            favorite_id=fav.id,
            status="sent" if success else "failed",
        )
        db.add(log)
    db.commit()


# ---------------------------------------------------------------------------
# 메인 파이프라인
# ---------------------------------------------------------------------------

async def crawl_and_notify() -> dict:
    """크롤링 → 파싱 → 저장 → 알림 파이프라인. 결과 dict 반환."""
    import time
    started = time.perf_counter()
    logger.info("=== 부고 크롤링 시작 ===")
    db = SessionLocal()
    new_count = 0
    skip_count = 0
    merge_count = 0
    url_skip_count = 0
    api_calls = 0

    try:
        _seen_urls.load_from_db(db)

        news_items, api_calls = await search_obituary_news()

        for item in news_items:
            url = item.original_link or item.naver_link

            if url in _seen_urls:
                url_skip_count += 1
                continue

            body = await fetch_article_text(item.naver_link or url)
            body_or_desc = body or item.description or ""
            # body·description 모두 없으면 제목만으로 파싱 — 고인 추출 어려움
            if not body_or_desc.strip():
                _seen_urls.add(url)
                skip_count += 1
                continue

            parsed_list = parse_obituary_multi(item.title, body_or_desc)

            _seen_urls.add(url)

            if not parsed_list:
                skip_count += 1
                continue

            valid = [p for p in parsed_list if p.deceased_name or p.key_person]
            if not valid:
                skip_count += 1
                continue

            for parsed in valid:
                obit, is_new = _merge_and_save(db, parsed, item.title, url, body_or_desc, item.pub_date)
                if obit is None:
                    continue
                if is_new:
                    new_count += 1
                    matched = _match_favorites(db, obit)
                    if matched:
                        logger.info(
                            "즐겨찾기 매칭 %d건 → 알림 발송 (핵심인물: %s)",
                            len(matched), obit.key_person or obit.title,
                        )
                        await _send_notifications(db, obit, matched)
                else:
                    merge_count += 1

        # 크롤링 직후 데이터 정리 (중복 제거, 병합, 품질 보정)
        try:
            from app.deduplication import run_cleanup
            cleanup_result = run_cleanup(db=db)
            if cleanup_result["total_changes"] > 0:
                logger.info(
                    "데이터 정리: 병합 %d건, 삭제 %d건, 보정 %d건",
                    cleanup_result["merged"], cleanup_result["deleted"], cleanup_result["corrected"],
                )
        except Exception as cleanup_err:
            logger.warning("데이터 정리 중 오류 (무시): %s", cleanup_err)

        duration = time.perf_counter() - started
        logger.info(
            "=== 크롤링 완료: 신규 %d건 / 보충 %d건 / 필터링 %d건 / URL스킵 %d건 (%.1f초, API %d회) ===",
            new_count, merge_count, skip_count, url_skip_count, duration, api_calls,
        )
    except Exception as e:
        duration = time.perf_counter() - started
        logger.exception("크롤링 작업 중 오류 발생: %s", e)
        raise
    finally:
        db.close()

    duration = time.perf_counter() - started
    return {
        "new_count": new_count,
        "merge_count": merge_count,
        "skip_count": skip_count,
        "url_skip_count": url_skip_count,
        "duration_seconds": round(duration, 1),
        "api_calls": api_calls,
    }


def run_crawl_job(app=None):
    """APScheduler에서 호출하는 동기 래퍼. app이 있으면 crawl_status 갱신."""
    from datetime import datetime
    if app and hasattr(app.state, "crawl_status"):
        app.state.crawl_status["is_running"] = True
        app.state.crawl_status["started_at"] = datetime.now()
    try:
        result = asyncio.run(crawl_and_notify())
        if app and hasattr(app.state, "crawl_status"):
            s = app.state.crawl_status
            s["last_run"] = datetime.now()
            s["last_count"] = result["new_count"]
            s["last_error"] = None
            s["duration_seconds"] = result["duration_seconds"]
            s["api_calls_this_run"] = result["api_calls"]
    except Exception as e:
        if app and hasattr(app.state, "crawl_status"):
            app.state.crawl_status["last_error"] = str(e)
        raise
    finally:
        if app and hasattr(app.state, "crawl_status"):
            app.state.crawl_status["is_running"] = False
