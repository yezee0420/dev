"""기존 DB의 부고 레코드를 새 파서로 재파싱하여 전체 덮어쓴다.

실행: python reparse_all.py

동작:
  - 모든 Obituary의 title + raw_text를 새 파서로 재파싱
  - 파싱된 값으로 해당 필드 전체 덮어쓰기 (204건 모두 적용)
"""

from __future__ import annotations

from app.database import SessionLocal, init_db
from app.models import Obituary
from app.crawler.parser import parse_obituary, ParsedObituary

_MERGE_FIELDS = (
    "deceased_name", "deceased_age", "funeral_hall", "room_number",
    "funeral_date", "funeral_time", "contact", "related_persons",
    "key_person", "organization", "position", "relationship",
)


def main() -> None:
    init_db()
    db = SessionLocal()

    rows = db.query(Obituary).order_by(Obituary.id).all()
    applied_count = 0
    skipped_count = 0

    for obit in rows:
        if not obit.title or not obit.raw_text:
            skipped_count += 1
            continue

        parsed = parse_obituary(obit.title, obit.raw_text)
        if parsed is None:
            skipped_count += 1
            continue

        for fld in _MERGE_FIELDS:
            new_val = getattr(parsed, fld, None)
            setattr(obit, fld, new_val)

        applied_count += 1

    db.commit()
    db.close()

    print(f"재파싱 완료: {applied_count}건 적용 (총 {len(rows)}건, 스킵 {skipped_count}건)")
    print("홈페이지 새로고침하면 변경 내용이 반영됩니다.")


if __name__ == "__main__":
    main()
