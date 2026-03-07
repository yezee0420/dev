"""매시간 실행되는 크롤링 작업 + 즐겨찾기 매칭 알림."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Obituary, Favorite, NotificationLog
from app.crawler.naver_api import search_obituary_news
from app.crawler.scraper import fetch_article_text
from app.crawler.parser import parse_obituary, make_dedup_key, ParsedObituary
from app.notifications.email_sender import EmailNotifier

logger = logging.getLogger(__name__)


def _find_existing(db: Session, dedup_key: str) -> Obituary | None:
    if not dedup_key:
        return None
    return db.query(Obituary).filter(Obituary.dedup_key == dedup_key).first()


def _merge_and_save(db: Session, parsed: ParsedObituary, title: str, url: str,
                     raw_text: str, pub_date: datetime | None) -> tuple[Obituary | None, bool]:
    """기존 레코드가 있으면 빈 필드를 보충하고, 없으면 새로 생성한다.
    (obituary, is_new) 튜플을 반환."""
    dedup_key = make_dedup_key(parsed)

    existing = _find_existing(db, dedup_key)
    if existing:
        updated = False
        # 빈 필드만 보충 업데이트
        for field in ["deceased_name", "deceased_age", "funeral_hall", "room_number",
                       "funeral_date", "funeral_time", "contact", "related_persons"]:
            old_val = getattr(existing, field)
            new_val = getattr(parsed, field, None)
            if not old_val and new_val:
                setattr(existing, field, new_val)
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
    matched: list[Favorite] = []

    searchable = " ".join(filter(None, [
        obit.key_person, obit.organization, obit.position,
        obit.deceased_name, obit.funeral_hall, obit.title,
        obit.related_persons, obit.raw_text,
    ]))

    for fav in favorites:
        if fav.keyword and fav.keyword in searchable:
            already_sent = (
                db.query(NotificationLog.id)
                .filter(
                    NotificationLog.obituary_id == obit.id,
                    NotificationLog.favorite_id == fav.id,
                )
                .first()
            )
            if not already_sent:
                matched.append(fav)

    return matched


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


async def crawl_and_notify() -> int:
    """크롤링 → 파싱 → 저장 → 알림 파이프라인을 실행한다. 신규 건수를 반환."""
    logger.info("=== 부고 크롤링 시작 ===")
    db = SessionLocal()
    new_count = 0
    skip_count = 0
    merge_count = 0

    try:
        news_items = await search_obituary_news()

        for item in news_items:
            url = item.original_link or item.naver_link

            body = await fetch_article_text(item.naver_link or url)
            parsed = parse_obituary(item.title, body or item.description)

            if parsed is None:
                skip_count += 1
                continue

            obit, is_new = _merge_and_save(db, parsed, item.title, url, body, item.pub_date)
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

        logger.info(
            "=== 크롤링 완료: 신규 %d건 / 보충 %d건 / 필터링 %d건 ===",
            new_count, merge_count, skip_count,
        )
    except Exception:
        logger.exception("크롤링 작업 중 오류 발생")
        raise
    finally:
        db.close()

    return new_count


def run_crawl_job():
    """APScheduler에서 호출하는 동기 래퍼."""
    asyncio.run(crawl_and_notify())
