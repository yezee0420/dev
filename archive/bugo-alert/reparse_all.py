"""기존 DB의 부고 레코드를 새 파서로 재파싱하여 전체 덮어쓴다.

실행: python reparse_all.py

동작:
  - 모든 Obituary의 title + raw_text를 새 파서로 재파싱
  - 복수 부고(민지홍 모친상, 유남석 장모상 등)는 key_person별로 행 분리
  - 파싱된 값으로 해당 필드 전체 덮어쓰기
"""

from __future__ import annotations

from app.database import SessionLocal, init_db
from app.models import Obituary
from app.crawler.parser import parse_obituary_multi, make_dedup_key

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
    split_count = 0

    for obit in rows:
        if not obit.title or not obit.raw_text:
            skipped_count += 1
            continue

        parsed_list = parse_obituary_multi(obit.title, obit.raw_text)
        if not parsed_list:
            skipped_count += 1
            continue

        first = parsed_list[0]
        for fld in _MERGE_FIELDS:
            new_val = getattr(first, fld, None)
            setattr(obit, fld, new_val)
        dk = make_dedup_key(first)
        if dk:
            db.flush()  # 이전 변경 반영 후 조회
            existing = db.query(Obituary).filter(Obituary.dedup_key == dk, Obituary.id != obit.id).first()
            obit.dedup_key = dk if not existing else None  # 충돌 시 None (fix_duplicates에서 통합)
        applied_count += 1

        for p in parsed_list[1:]:
            dk = make_dedup_key(p)
            if dk and db.query(Obituary).filter(Obituary.dedup_key == dk).first():
                continue  # 이미 같은 dedup_key 행 있으면 스킵 (fix_duplicates에서 통합)
            new_row = Obituary(
                source_url=obit.source_url,
                title=obit.title,
                key_person=p.key_person,
                organization=p.organization,
                position=p.position,
                deceased_name=p.deceased_name,
                deceased_age=p.deceased_age,
                relationship=p.relationship,
                related_persons=p.related_persons,
                funeral_hall=p.funeral_hall,
                room_number=p.room_number,
                funeral_date=p.funeral_date,
                funeral_time=p.funeral_time,
                contact=p.contact,
                raw_text=obit.raw_text[:5000] if obit.raw_text else None,
                published_at=obit.published_at,
                dedup_key=dk,
            )
            db.add(new_row)
            split_count += 1

    db.commit()
    db.close()

    print(f"재파싱 완료: {applied_count}건 적용, 복수 key 분리 {split_count}건 (총 {len(rows)}건, 스킵 {skipped_count}건)")
    print("홈페이지 새로고침하면 변경 내용이 반영됩니다.")


if __name__ == "__main__":
    main()
