#!/usr/bin/env python3
"""기존 레코드의 source_url에서 기사를 재수집하여 빈 필드를 보충한다.

고인·장례식장 등이 비어 있는 레코드는 예전 크롤링 시 잘못된 raw_text(네이버 래퍼 등)로
저장되었을 수 있다. 이 스크립트로 재수집 후 파싱하여 빈 칸을 채운다.

실행: cd bugo-alert && PYTHONPATH=. python scripts/backfill_from_source.py
옵션:
  --dry-run     DB 변경 없이 예정만 출력
  --limit N     최대 N건만 처리 (기본 100)
  --key-person  특정 핵심인물만 (예: --key-person 이창석)
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.database import SessionLocal
from app.models import Obituary
from app.crawler.scraper import fetch_article_text
from app.crawler.parser import parse_obituary, make_dedup_key

_FILL_FIELDS = (
    "deceased_name", "deceased_age", "funeral_hall", "room_number",
    "funeral_date", "funeral_time", "contact", "related_persons",
    "organization", "position", "relationship",
)


def _fill_blank_fields(obit: Obituary, parsed) -> bool:
    """빈 필드를 새 파싱 결과로 보충."""
    updated = False
    for fld in _FILL_FIELDS:
        old_val = getattr(obit, fld)
        new_val = getattr(parsed, fld, None)
        if not old_val and new_val:
            setattr(obit, fld, new_val)
            updated = True
    return updated


async def _process_one(obit: Obituary, dry_run: bool) -> bool:
    """한 레코드를 재수집·파싱하여 보충. 성공 시 True."""
    url = obit.source_url
    if not url or not url.startswith(("http://", "https://")):
        return False

    body = await fetch_article_text(url)
    if not body or len(body.strip()) < 30:
        return False

    parsed = parse_obituary(obit.title or "", body)
    if not parsed:
        return False

    updated = _fill_blank_fields(obit, parsed)
    if updated:
        if parsed.deceased_name and not obit.dedup_key:
            obit.dedup_key = make_dedup_key(parsed)
        obit.raw_text = (body[:5000] if body else None)
        if not dry_run:
            return True
    return updated


async def main():
    parser = argparse.ArgumentParser(description="기존 레코드 재수집으로 빈 필드 보충")
    parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 출력만")
    parser.add_argument("--limit", type=int, default=100, help="최대 처리 건수")
    parser.add_argument("--key-person", type=str, help="특정 핵심인물만 (예: 이창석)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        q = db.query(Obituary).filter(
            Obituary.deceased_name.is_(None) | (Obituary.deceased_name == ""),
        )
        if args.key_person:
            q = q.filter(Obituary.key_person == args.key_person)
        rows = q.limit(args.limit).all()

        if not rows:
            print("보충 대상 레코드 없음")
            return

        print(f"대상 {len(rows)}건 (dry_run={args.dry_run})")
        ok = 0
        for obit in rows:
            u = await _process_one(obit, args.dry_run)
            if u:
                ok += 1
                print(f"  id={obit.id} key_person={obit.key_person} → deceased={obit.deceased_name} hall={obit.funeral_hall} contact={obit.contact}")

        if not args.dry_run and ok > 0:
            db.commit()
        print(f"보충 완료 {ok}건")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
