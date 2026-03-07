"""매시간 실행되는 크롤링 작업 + 즐겨찾기 매칭 알림."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Obituary, Favorite, NotificationLog
from app.crawler.naver_api import search_obituary_news
from app.crawler.scraper import fetch_article_text
from app.crawler.parser import parse_obituary, ParsedObituary
from app.notifications.email_sender import EmailNotifier

logger = logging.getLogger(__name__)


def _obituary_exists(db: Session, source_url: str) -> bool:
    return db.query(Obituary.id).filter(Obituary.source_url == source_url).first() is not None


def _save_obituary(db: Session, parsed: ParsedObituary, title: str, url: str,
                    raw_text: str, pub_date: datetime | None) -> Obituary:
    obit = Obituary(
        source_url=url,
        title=title,
        deceased_name=parsed.deceased_name,
        age=parsed.age,
        organization=parsed.organization,
        position=parsed.position,
        relationship=parsed.relationship,
        mourner_name=parsed.mourner_name,
        funeral_hall=parsed.funeral_hall,
        room_number=parsed.room_number,
        funeral_date=parsed.funeral_date,
        funeral_time=parsed.funeral_time,
        contact=parsed.contact,
        remarks=parsed.remarks,
        raw_text=raw_text[:5000] if raw_text else None,
        published_at=pub_date,
    )
    db.add(obit)
    db.commit()
    db.refresh(obit)
    return obit


def _match_favorites(db: Session, obit: Obituary) -> list[Favorite]:
    """부고 정보와 즐겨찾기 키워드를 매칭한다."""
    favorites = db.query(Favorite).filter(Favorite.is_active == True).all()
    matched: list[Favorite] = []

    searchable = " ".join(filter(None, [
        obit.deceased_name, obit.organization, obit.position,
        obit.mourner_name, obit.funeral_hall, obit.title, obit.raw_text,
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


async def crawl_and_notify():
    """크롤링 → 파싱 → 저장 → 알림 파이프라인을 실행한다."""
    logger.info("=== 부고 크롤링 시작 ===")
    db = SessionLocal()

    try:
        news_items = await search_obituary_news()
        new_count = 0

        for item in news_items:
            url = item.original_link or item.naver_link
            if not url or _obituary_exists(db, url):
                continue

            body = await fetch_article_text(item.naver_link or url)
            parsed_list = parse_obituary(item.title, body or item.description)

            if not parsed_list:
                parsed_list = [ParsedObituary()]

            for parsed in parsed_list:
                obit = _save_obituary(db, parsed, item.title, url, body, item.pub_date)
                new_count += 1

                matched = _match_favorites(db, obit)
                if matched:
                    logger.info(
                        "즐겨찾기 매칭 %d건 → 알림 발송 (부고: %s)",
                        len(matched), obit.deceased_name or obit.title,
                    )
                    await _send_notifications(db, obit, matched)

        logger.info("=== 크롤링 완료: 신규 %d건 저장 ===", new_count)
    except Exception:
        logger.exception("크롤링 작업 중 오류 발생")
    finally:
        db.close()


def run_crawl_job():
    """APScheduler에서 호출하는 동기 래퍼."""
    asyncio.run(crawl_and_notify())
